//! OTLP is a diagnostic replica. Export failures never decide delivery.
use std::{
    fs::{self, OpenOptions},
    io::Write as _,
    path::{Path, PathBuf},
    sync::{
        Arc,
        atomic::{AtomicU64, Ordering},
        mpsc,
    },
    time::{Duration, Instant, SystemTime},
};

use anyhow::{Context as _, Result, ensure};
use opentelemetry::{
    KeyValue, global,
    logs::{LogRecord as _, Logger as _, LoggerProvider as _, Severity},
    trace::{Span as _, Status, Tracer as _, TracerProvider as _},
};
use opentelemetry_appender_tracing::layer::OpenTelemetryTracingBridge;
use opentelemetry_http::{Bytes, HttpClient, HttpError, Request, Response};
use opentelemetry_otlp::{Protocol, WithExportConfig as _, WithHttpConfig as _};
use opentelemetry_sdk::{
    Resource,
    logs::{BatchConfigBuilder, BatchLogProcessor, SdkLogger, SdkLoggerProvider},
    metrics::SdkMeterProvider,
    trace::SdkTracerProvider,
};
use serde_json::{Value, json};
use tracing_opentelemetry::OpenTelemetrySpanExt as _;
use tracing_subscriber::{
    EnvFilter, Layer as _, layer::SubscriberExt as _, util::SubscriberInitExt as _,
};

pub fn configured() -> bool {
    [
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    ]
    .iter()
    .any(|name| std::env::var(name).is_ok_and(|value| !value.trim().is_empty()))
}

pub fn local_logging() {
    let _ = tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .try_init();
}

pub fn diagnostic(state: &Path, detail: &Value) {
    let result = (|| -> std::io::Result<()> {
        fs::create_dir_all(state)?;
        let mut options = OpenOptions::new();
        options.create(true).append(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt as _;
            options.mode(0o600);
        }
        let mut file = options.open(state.join("telemetry-errors.jsonl"))?;
        writeln!(
            file,
            "{}",
            &json!({"time":SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap_or_default().as_secs_f64(),"detail":detail})
        )
    })();
    if let Err(error) = result {
        eprintln!("cannot preserve telemetry diagnostic: {error}");
    }
    eprintln!("OTLP diagnostic recorded in {}", state.join("telemetry-errors.jsonl").display());
}

/// reqwest's stock `OTel` adapter calls `error_for_status` before reading the body.
/// Keep the original response and transport cause locally, without logging headers.
#[derive(Debug, Clone)]
struct DiagnosticClient {
    client: reqwest::blocking::Client,
    state: PathBuf,
    failures: Arc<AtomicU64>,
}
#[async_trait::async_trait]
impl HttpClient for DiagnosticClient {
    async fn send_bytes(
        &self,
        request: Request<Bytes>,
    ) -> std::result::Result<Response<Bytes>, HttpError> {
        let signal = request.uri().path().to_owned();
        let result = (|| -> std::result::Result<Response<Bytes>, HttpError> {
            // Our evidence records are bounded; this also catches accidental oversized spans.
            if request.body().len() >= 16 * 1024 * 1024 {
                return Err("OTLP batch exceeds collector's 16 MiB limit".into());
            }
            let mut request: reqwest::blocking::Request = request.try_into()?;
            let kind = signal.rsplit('/').next().unwrap_or("").to_uppercase();
            let timeout = std::env::var(format!("OTEL_EXPORTER_OTLP_{kind}_TIMEOUT"))
                .or_else(|_| std::env::var("OTEL_EXPORTER_OTLP_TIMEOUT"))
                .ok()
                .and_then(|s| s.parse::<u64>().ok())
                .unwrap_or(10_000);
            *request.timeout_mut() = Some(Duration::from_millis(timeout));
            let mut response = self.client.execute(request)?;
            let status = response.status();
            let headers = std::mem::take(response.headers_mut());
            let body = response.bytes()?;
            if !status.is_success() {
                self.failures.fetch_add(1, Ordering::Relaxed);
                diagnostic(
                    &self.state,
                    &json!({"signal":signal,"http_status":status.as_u16(),"response_body":String::from_utf8_lossy(&body)}),
                );
            }
            let mut output = Response::builder().status(status).body(body)?;
            *output.headers_mut() = headers;
            Ok(output)
        })();
        if let Err(error) = &result {
            self.failures.fetch_add(1, Ordering::Relaxed);
            diagnostic(&self.state, &json!({"signal":signal,"error":format!("{error:?}")}));
        }
        result
    }
}

pub struct TelemetryGuard {
    tracer: SdkTracerProvider,
    meter: SdkMeterProvider,
    logger: SdkLoggerProvider,
    evidence: SdkLoggerProvider,
    failures: Arc<AtomicU64>,
    state: PathBuf,
}

impl TelemetryGuard {
    // Construct and shut down blocking HTTP clients outside the Tokio runtime.
    pub fn install(state: PathBuf, run_id: &str) -> Result<Self> {
        for signal in ["", "_TRACES", "_LOGS", "_METRICS"] {
            let name = format!("OTEL_EXPORTER_OTLP{signal}_PROTOCOL");
            if let Ok(value) = std::env::var(&name) {
                ensure!(value == "http/protobuf", "{name} must be http/protobuf");
            }
            let name = format!("OTEL_EXPORTER_OTLP{signal}_COMPRESSION");
            if let Ok(value) = std::env::var(&name) {
                ensure!(value.is_empty() || value == "none", "{name} must be none");
            }
        }
        let failures = Arc::new(AtomicU64::new(0));
        let client = DiagnosticClient {
            client: reqwest::blocking::Client::builder()
                .timeout(Duration::from_secs(3))
                .redirect(reqwest::redirect::Policy::none())
                .build()?,
            state: state.clone(),
            failures: Arc::clone(&failures),
        };
        let resource = Resource::builder()
            .with_service_name("braid")
            .with_attributes([
                KeyValue::new("service.version", env!("CARGO_PKG_VERSION")),
                KeyValue::new("service.instance.id", uuid::Uuid::now_v7().to_string()),
                KeyValue::new("braid.run.id", run_id.to_owned()),
            ])
            .build();
        let tracer = SdkTracerProvider::builder()
            .with_resource(resource.clone())
            .with_batch_exporter(
                opentelemetry_otlp::SpanExporter::builder()
                    .with_http()
                    .with_protocol(Protocol::HttpBinary)
                    .with_http_client(client.clone())
                    .build()?,
            )
            .build();
        let meter = SdkMeterProvider::builder()
            .with_resource(resource.clone())
            .with_periodic_exporter(
                opentelemetry_otlp::MetricExporter::builder()
                    .with_http()
                    .with_protocol(Protocol::HttpBinary)
                    .with_http_client(client.clone())
                    .build()?,
            )
            .build();
        let logger = SdkLoggerProvider::builder()
            .with_resource(resource.clone())
            .with_batch_exporter(
                opentelemetry_otlp::LogExporter::builder()
                    .with_http()
                    .with_protocol(Protocol::HttpBinary)
                    .with_http_client(client.clone())
                    .build()?,
            )
            .build();
        // A dedicated bounded evidence queue cannot be filled by provider diagnostics.
        let processor = BatchLogProcessor::builder(
            opentelemetry_otlp::LogExporter::builder()
                .with_http()
                .with_protocol(Protocol::HttpBinary)
                .with_http_client(client)
                .build()?,
        )
        .with_batch_config(
            BatchConfigBuilder::default()
                .with_max_export_batch_size(64)
                .with_max_queue_size(256)
                .build(),
        )
        .build();
        let evidence = SdkLoggerProvider::builder()
            .with_resource(resource)
            .with_log_processor(processor)
            .build();
        let trace_layer = tracing_opentelemetry::layer()
            .with_tracer(tracer.tracer("braid"))
            .with_filter(EnvFilter::new("off,braid=info"));
        let log_layer =
            OpenTelemetryTracingBridge::new(&logger).with_filter(EnvFilter::new("off,braid=info"));
        let fmt_layer = tracing_subscriber::fmt::layer().with_writer(std::io::stderr).with_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        );
        tracing_subscriber::registry()
            .with(trace_layer)
            .with(log_layer)
            .with(fmt_layer)
            .try_init()?;
        global::set_tracer_provider(tracer.clone());
        global::set_meter_provider(meter.clone());
        Ok(Self { tracer, meter, logger, evidence, failures, state })
    }

    pub fn evidence_writer(&self) -> EvidenceWriter {
        EvidenceWriter {
            logger: self.evidence.logger("braid.evidence"),
            provider: self.evidence.clone(),
            failures: Arc::clone(&self.failures),
            pending: 0,
            observed_failures: self.failures.load(Ordering::Relaxed),
        }
    }

    pub fn shutdown(self) -> Result<()> {
        let mut errors = Vec::new();
        for (signal, result) in [
            ("evidence", self.evidence.shutdown()),
            ("logs", self.logger.shutdown()),
            ("traces", self.tracer.shutdown()),
            ("metrics", self.meter.shutdown()),
        ] {
            if let Err(error) = result {
                diagnostic(
                    &self.state,
                    &json!({"signal":signal,"shutdown_error":error.to_string()}),
                );
                errors.push(format!("{signal}: {error}"));
            }
        }
        ensure!(
            errors.is_empty() && self.failures.load(Ordering::Relaxed) == 0,
            "OTLP export had failures; see telemetry-errors.jsonl"
        );
        Ok(())
    }
}

pub struct EvidenceWriter {
    logger: SdkLogger,
    provider: SdkLoggerProvider,
    failures: Arc<AtomicU64>,
    observed_failures: u64,
    pending: usize,
}
impl EvidenceWriter {
    pub fn emit(&mut self, value: &Value) -> Result<bool> {
        let body = serde_json::to_string(value)?;
        ensure!(
            body.len() <= 192 * 1024,
            "evidence record exceeds 192 KiB; split the source record"
        );
        let mut record = self.logger.create_log_record();
        record.set_timestamp(SystemTime::now());
        record.set_severity_number(Severity::Info);
        record.set_event_name("braid.evidence");
        record.set_body(body.into());
        if let Some(kind) = value["event_kind"].as_str() {
            record.add_attribute("event.kind", kind.to_owned());
        }
        if let Some(id) = value["run_id"].as_str() {
            record.add_attribute("braid.run.id", id.to_owned());
        }
        self.logger.emit(record);
        self.pending += 1;
        if self.pending >= 64 {
            self.flush()?;
            return Ok(true);
        }
        Ok(false)
    }
    pub fn flush(&mut self) -> Result<()> {
        let pending = self.pending;
        let started = Instant::now();
        let result = self.provider.force_flush();
        self.pending = 0;
        let failures = self.failures.load(Ordering::Relaxed);
        let prior = std::mem::replace(&mut self.observed_failures, failures);
        result.with_context(|| {
            format!("evidence flush: {pending} records, {} ms", started.elapsed().as_millis())
        })?;
        ensure!(prior == failures, "OTLP transport failed; see telemetry-errors.jsonl");
        Ok(())
    }
}

/// Lives across awaits without entering a thread-local span guard.
pub struct Operation {
    span: global::BoxedSpan,
    started: Instant,
    name: &'static str,
    result: String,
}
impl Operation {
    pub fn new(name: &'static str, attributes: Vec<KeyValue>) -> Self {
        let context = tracing::Span::current().context();
        let span = global::tracer("braid")
            .span_builder(name)
            .with_attributes(attributes)
            .start_with_context(&global::tracer("braid"), &context);
        global::meter("braid")
            .i64_up_down_counter("braid.operations.active")
            .build()
            .add(1, &[KeyValue::new("operation", name)]);
        Self { span, started: Instant::now(), name, result: "unknown".into() }
    }
    pub fn attribute(&mut self, key: &'static str, value: String) {
        self.span.set_attribute(KeyValue::new(key, value));
    }
    pub fn finish(&mut self, result: &str) {
        result.clone_into(&mut self.result);
        self.span.set_attribute(KeyValue::new("result", self.result.clone()));
        self.span.set_status(if matches!(result, "completed" | "ok") {
            Status::Ok
        } else {
            Status::error(result.to_owned())
        });
    }
}
impl Drop for Operation {
    fn drop(&mut self) {
        let attributes =
            [KeyValue::new("operation", self.name), KeyValue::new("result", self.result.clone())];
        self.span.set_attribute(attributes[1].clone());
        self.span.end();
        let meter = global::meter("braid");
        measurement(self.name, &self.result, self.started.elapsed().as_secs_f64());
        meter
            .i64_up_down_counter("braid.operations.active")
            .build()
            .add(-1, &[KeyValue::new("operation", self.name)]);
    }
}

pub fn measurement(operation: &'static str, result: &str, seconds: f64) {
    let attributes =
        [KeyValue::new("operation", operation), KeyValue::new("result", result.to_owned())];
    let meter = global::meter("braid");
    meter.u64_counter("braid.operations").build().add(1, &attributes);
    meter
        .f64_histogram("braid.operation.duration")
        .with_unit("s")
        .build()
        .record(seconds, &attributes);
}

fn record_usage(summary: &Value) {
    let meter = global::meter("braid");
    if let Some(count) = summary["inventory"]["artifacts"].as_u64() {
        meter.u64_gauge("braid.evidence.source.artifacts").build().record(count, &[]);
    }
    if let Some(bytes) = summary["inventory"]["bytes"].as_u64() {
        meter.u64_gauge("braid.evidence.source.bytes").with_unit("By").build().record(bytes, &[]);
    }
    if let Some(count) = summary["native_sessions"].as_u64() {
        meter.u64_gauge("braid.sessions.observed").build().record(count, &[]);
    }
    if let Some(rows) = summary["usage"].as_array() {
        for row in rows {
            let Some(tokens) = row["tokens"].as_object() else { continue };
            for (kind, value) in tokens {
                let Some(value) = value.as_u64() else { continue };
                let attributes = [
                    KeyValue::new(
                        "provider",
                        row["provider"].as_str().unwrap_or("unknown").to_owned(),
                    ),
                    KeyValue::new("model", row["model"].as_str().unwrap_or("unknown").to_owned()),
                    KeyValue::new("token.type", kind.clone()),
                ];
                meter.u64_gauge("braid.tokens.observed").build().record(value, &attributes);
                if let Some(count) = row["known_messages"][kind].as_u64() {
                    meter
                        .u64_gauge("braid.token_usage.messages")
                        .build()
                        .record(count, &attributes);
                }
            }
        }
    }
}

pub struct EvidenceWorker {
    stop: mpsc::Sender<()>,
    thread: std::thread::JoinHandle<()>,
}

fn capture_memory() -> Value {
    match fs::read_to_string("/proc/self/status") {
        Ok(status) => {
            let fields: serde_json::Map<String, Value> = status
                .lines()
                .filter_map(|line| {
                    let (key, value) = line.split_once(':')?;
                    matches!(
                        key,
                        "VmRSS" | "VmHWM" | "RssAnon" | "RssFile" | "RssShmem" | "Threads"
                    )
                    .then(|| (key.to_owned(), json!(value.trim())))
                })
                .collect();
            Value::Object(fields)
        }
        Err(error) => json!({"error":error.to_string()}),
    }
}

fn capture_observation(state: &Path, observation: &Value) {
    if let Err(error) =
        crate::local::write_json(&state.join("evidence-capture-latest.json"), observation)
    {
        tracing::warn!(%error, "cannot preserve evidence capture memory observation");
    }
}

impl EvidenceWorker {
    pub fn start(state: PathBuf, run_id: String, mut writer: EvidenceWriter) -> Self {
        let (stop, signal) = mpsc::channel();
        let thread = std::thread::spawn(move || {
            let mut collector = crate::evidence::EvidenceCollector::new(run_id.clone());
            loop {
                let final_capture = !matches!(
                    // Evidence includes durable object snapshots; capture less often than live logs.
                    // stop still wakes this wait immediately for the final capture.
                    signal.recv_timeout(Duration::from_secs(30)),
                    Err(mpsc::RecvTimeoutError::Timeout)
                );
                if state.join("braid.sqlite3").is_file() {
                    let started = Instant::now();
                    let before = capture_memory();
                    let observed_at = SystemTime::now()
                        .duration_since(SystemTime::UNIX_EPOCH)
                        .unwrap_or_default()
                        .as_nanos()
                        .to_string();
                    capture_observation(
                        &state,
                        &json!({"phase":"started", "observed_at_unix_nanos":observed_at,
                        "pid":std::process::id(), "final_capture":final_capture, "memory_before":before}),
                    );
                    let result = collector
                        .capture(
                            &state,
                            None,
                            final_capture,
                            crate::evidence::CaptureMode::Summary,
                            &mut |v| writer.emit(v),
                        )
                        .and_then(|summary| {
                            writer.flush()?;
                            collector.flush_succeeded();
                            record_usage(&summary);
                            Ok(())
                        });
                    capture_observation(
                        &state,
                        &json!({"phase":"finished", "observed_at_unix_nanos":observed_at,
                        "pid":std::process::id(), "final_capture":final_capture,
                        "elapsed_ms":started.elapsed().as_millis(), "memory_before":before,
                        "memory_after":capture_memory(), "error":result.as_ref().err().map(ToString::to_string)}),
                    );
                    if let Err(error) = result {
                        diagnostic(
                            &state,
                            &json!({"capture_error":format!("{error:#}"),
                            "capture_elapsed_ms":started.elapsed().as_millis(),
                            "final_capture":final_capture}),
                        );
                        // Retry only records emitted since the last successful flush.
                        collector.retry_since_flush();
                    }
                }
                if final_capture {
                    break;
                }
            }
        });
        Self { stop, thread }
    }
    pub fn stop(self) {
        let _ = self.stop.send(());
        let _ = self.thread.join();
    }
}

pub async fn initialize(state: &Path, run_id: &str) -> Option<TelemetryGuard> {
    if !configured() {
        local_logging();
        return None;
    }
    let path = state.to_owned();
    let id = run_id.to_owned();
    match tokio::task::spawn_blocking(move || TelemetryGuard::install(path, &id)).await {
        Ok(Ok(guard)) => Some(guard),
        Ok(Err(error)) => {
            diagnostic(state, &json!({"initialization_error":format!("{error:#}")}));
            local_logging();
            None
        }
        Err(error) => {
            diagnostic(state, &json!({"initialization_error":error.to_string()}));
            local_logging();
            None
        }
    }
}

pub async fn export(
    state: PathBuf,
    native_manifest: Option<PathBuf>,
    portable: bool,
) -> Result<Value> {
    ensure!(configured(), "OTEL_EXPORTER_OTLP_ENDPOINT is required");
    let connection = rusqlite::Connection::open_with_flags(
        state.join("braid.sqlite3"),
        rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY,
    )?;
    let run_id: String = connection.query_row("SELECT run_id FROM local_run", [], |r| r.get(0))?;
    drop(connection);
    let state_copy = state.clone();
    tokio::task::spawn_blocking(move || {
        let guard = TelemetryGuard::install(state.clone(), &run_id)?;
        let mut operation = Operation::new("braid.telemetry.export", vec![]);
        let mut writer = guard.evidence_writer();
        let mode = if portable {
            crate::evidence::CaptureMode::Portable
        } else {
            crate::evidence::CaptureMode::Summary
        };
        let result = crate::evidence::EvidenceCollector::new(run_id)
            .capture(&state, native_manifest.as_deref(), true, mode, &mut |v| writer.emit(v))
            .and_then(|summary| {
                writer.flush()?;
                Ok(summary)
            });
        operation.finish(if result.is_ok() { "ok" } else { "failed" });
        drop(operation);
        let shutdown = guard.shutdown();
        result.and_then(|summary| {
            shutdown?;
            Ok(summary)
        })
    })
    .await
    .context("telemetry export worker failed")?
    .inspect_err(|error| diagnostic(&state_copy, &json!({"export_error":format!("{error:#}")})))
}
