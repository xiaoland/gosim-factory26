mod config;
mod usage;

use axum::{
    Json, Router,
    body::{Body, to_bytes},
    extract::{Request, State},
    http::{HeaderMap, StatusCode, header},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use config::{Config, Route};
use futures_util::StreamExt;
use hyper_util::{
    rt::{TokioIo, TokioTimer},
    service::TowerToHyperService,
};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet},
    io::{self, Write},
    path::PathBuf,
    sync::{
        Arc,
        atomic::{AtomicU64, Ordering},
    },
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tokio::{
    net::TcpListener,
    task::JoinSet,
    time::{Instant, timeout, timeout_at},
};
use tokio_util::sync::CancellationToken;

fn ms(value: u64) -> Duration {
    Duration::from_millis(value)
}

struct App {
    config: Config,
    routes: BTreeMap<String, Vec<Route>>,
    client: reqwest::Client,
    token: String,
    secrets: Vec<String>,
    config_sha: String,
    next: AtomicU64,
}

impl App {
    fn log(&self, mut value: Value) {
        value["run_id"] = json!(self.config.run_id);
        value["config_sha256"] = json!(self.config_sha);
        value["timestamp_ms"] = json!(
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis()
        );
        let mut line = value.to_string();
        for secret in &self.secrets {
            if !secret.is_empty() {
                line = line.replace(secret, "[credential]");
            }
        }
        let mut output = io::stdout().lock();
        let _ = writeln!(output, "{line}");
    }
}

struct RequestLife {
    app: Arc<App>,
    id: u64,
    alias: String,
    deployment: String,
    committed: bool,
    ended: bool,
}

impl RequestLife {
    fn event(&self, event: &str, details: Value) {
        self.app.log(
            json!({"event": event, "request_id": self.id, "alias": self.alias,
                            "deployment_id": self.deployment, "committed": self.committed,
                            "details": details}),
        );
    }
    fn end(&mut self, reason: &str) {
        self.event("terminal", json!({"reason": reason}));
        self.ended = true;
    }
}

impl Drop for RequestLife {
    fn drop(&mut self) {
        if !self.ended {
            self.end("downstream_or_connection_closed");
        }
    }
}

fn error(status: StatusCode, code: &str) -> Response {
    (
        status,
        Json(json!({"error": {"type": "model_proxy", "code": code}})),
    )
        .into_response()
}

fn body_read_diagnostic(error: &axum::Error) -> String {
    use std::error::Error;
    let mut diagnostic = error.to_string();
    let mut source = error.source();
    for _ in 0..8 {
        let Some(current) = source else { break };
        diagnostic.push_str(": ");
        diagnostic.push_str(&current.to_string());
        source = current.source();
    }
    diagnostic.chars().take(4096).collect()
}

const OUTPUT_BUDGET_FIELDS: [&str; 3] =
    ["max_tokens", "max_output_tokens", "max_completion_tokens"];

fn requested_output_limit(payload: &Value) -> Result<(Option<u64>, Vec<String>), Response> {
    let mut fields = Vec::new();
    for name in OUTPUT_BUDGET_FIELDS {
        let Some(value) = payload.get(name) else {
            continue;
        };
        if value.is_null() {
            continue;
        }
        let Some(value) = value.as_u64() else {
            return Err(error(StatusCode::BAD_REQUEST, "invalid_output_budget"));
        };
        fields.push((name, value));
    }
    let values: BTreeSet<u64> = fields.iter().map(|(_, value)| *value).collect();
    if values.len() > 1 {
        return Err(error(StatusCode::BAD_REQUEST, "conflicting_output_budgets"));
    }
    Ok((
        values.into_iter().next(),
        fields
            .into_iter()
            .map(|(name, _)| name.to_owned())
            .collect(),
    ))
}

fn transport_diagnostic(cause: reqwest::Error) -> String {
    use std::error::Error;
    let cause = cause.without_url();
    let mut diagnostic = cause.to_string();
    let mut source = cause.source();
    for _ in 0..8 {
        let Some(current) = source else { break };
        diagnostic.push_str(": ");
        diagnostic.push_str(&current.to_string());
        source = current.source();
    }
    diagnostic.chars().take(4096).collect()
}

fn response_headers(source: &HeaderMap) -> HeaderMap {
    // Hop-by-hop fields describe the upstream connection, not the local one.
    let mut headers = source.clone();
    if let Some(names) = source.get(header::CONNECTION).and_then(|v| v.to_str().ok()) {
        for name in names.split(',') {
            headers.remove(name.trim());
        }
    }
    for name in [
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "content-length",
    ] {
        headers.remove(name);
    }
    headers
}

async fn health() -> Json<Value> {
    Json(json!({"status": "ready"}))
}

async fn chat(State(app): State<Arc<App>>, request: Request) -> Response {
    let authorized = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "))
        .is_some_and(|v| v == app.token);
    if !authorized {
        return error(StatusCode::UNAUTHORIZED, "invalid_local_token");
    }
    let deadline = Instant::now() + ms(app.config.limits.total_ms);
    let mut life = RequestLife {
        app: app.clone(),
        id: app.next.fetch_add(1, Ordering::Relaxed),
        alias: String::new(),
        deployment: String::new(),
        committed: false,
        ended: false,
    };
    life.event("accepted", json!({}));
    let bytes = match timeout(
        ms(app.config.limits.body_ms),
        to_bytes(request.into_body(), usize::MAX),
    )
    .await
    {
        Ok(Ok(bytes)) => bytes,
        Ok(Err(cause)) => {
            let diagnostic = body_read_diagnostic(&cause);
            life.event("body_read_error", json!({"diagnostic": diagnostic}));
            life.end("body_read_error");
            return error(StatusCode::BAD_REQUEST, "body_read_error");
        }
        Err(_) => {
            life.end("body_timeout");
            return error(StatusCode::REQUEST_TIMEOUT, "body_timeout");
        }
    };
    let mut payload: Value = match serde_json::from_slice(&bytes) {
        Ok(Value::Object(object)) => Value::Object(object),
        _ => {
            life.end("invalid_json_object");
            return error(StatusCode::BAD_REQUEST, "invalid_json_object");
        }
    };
    drop(bytes);
    let Some(alias) = payload.get("model").and_then(Value::as_str) else {
        life.end("missing_model");
        return error(StatusCode::BAD_REQUEST, "missing_model");
    };
    life.alias = alias.to_owned();
    let Some(chain) = app.routes.get(alias) else {
        life.end("unknown_model");
        return error(StatusCode::BAD_REQUEST, "unknown_model");
    };
    let (requested_output_limit, requested_output_fields) = match requested_output_limit(&payload) {
        Ok(value) => value,
        Err(response) => {
            life.end("invalid_output_budget");
            return response;
        }
    };
    let requested_stream = payload
        .get("stream")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    let original_output_values: Vec<(String, Value)> = requested_output_fields
        .iter()
        .filter_map(|name| {
            payload
                .get(name)
                .cloned()
                .map(|value| (name.clone(), value))
        })
        .collect();
    for (index, route) in chain.iter().enumerate() {
        let attempt_started = Instant::now();
        life.deployment = route.deployment.deployment_id.clone();
        payload["model"] = json!(route.deployment.wire_model);
        for (name, value) in &original_output_values {
            payload[name] = value.clone();
        }
        let provider_limit = route
            .deployment
            .model_info
            .get("maxTokens")
            .and_then(Value::as_u64);
        let effective_output_limit = requested_output_limit
            .zip(provider_limit)
            .map(|(requested, limit)| requested.min(limit));
        if let Some(effective) = effective_output_limit {
            for name in &requested_output_fields {
                payload[name.as_str()] = json!(effective);
            }
        }
        let request = match app
            .client
            .post(route.url.clone())
            .header(header::AUTHORIZATION, route.auth.clone())
            .header(header::ACCEPT_ENCODING, "identity")
            .json(&payload)
            .build()
        {
            Ok(request) => request,
            Err(cause) => {
                life.event(
                    "request_build_error",
                    json!({"attempt": index + 1, "elapsed_ms": attempt_started.elapsed().as_millis(),
                        "diagnostic": transport_diagnostic(cause)}),
                );
                life.end("request_build_error");
                return error(StatusCode::BAD_REQUEST, "request_build_error");
            }
        };
        let request_body_bytes = request
            .body()
            .and_then(|body| body.as_bytes())
            .map_or(0, |body| body.len());
        life.event("attempt", json!({"attempt": index + 1, "provider": route.deployment.provider,
            "plan": route.deployment.plan, "wire_model": route.deployment.wire_model, "stream": requested_stream,
            "request_body_bytes": request_body_bytes,
            "output_limit": {"requested": requested_output_limit, "effective": effective_output_limit,
                              "deployment": route.deployment.deployment_id,
                              "source": provider_limit.map(|_| "catalog.model_info.maxTokens")}}));
        let sent = timeout_at(
            deadline.min(Instant::now() + ms(app.config.limits.headers_ms)),
            app.client.execute(request),
        )
        .await;
        let response = match sent {
            Ok(Ok(response)) => response,
            Ok(Err(cause)) => {
                // A header timeout may follow upstream execution; do not replay it.
                let connect = cause.is_connect();
                life.event(
                    "transport_error",
                    json!({"attempt": index + 1, "connect": connect,
                    "elapsed_ms": attempt_started.elapsed().as_millis(),
                    "diagnostic": transport_diagnostic(cause)}),
                );
                if connect && index + 1 < chain.len() {
                    continue;
                }
                life.end("transport_error");
                return error(StatusCode::BAD_GATEWAY, "upstream_transport_error");
            }
            Err(_) => {
                life.end("headers_or_total_timeout");
                return error(StatusCode::GATEWAY_TIMEOUT, "upstream_headers_timeout");
            }
        };
        let status = response.status();
        life.event(
            "upstream_headers",
            json!({"attempt": index + 1, "http_status": status.as_u16(),
            "elapsed_ms": attempt_started.elapsed().as_millis(),
            "request_id": response.headers().get("x-request-id").and_then(|v| v.to_str().ok())}),
        );
        let headers = response_headers(response.headers());
        if !status.is_success() {
            // Inspect the bounded error once, before any response is committed.
            let (diagnostic, truncated) = read_error(response, deadline, &app).await;
            let subscription_expired = status.as_u16() == 401
                && matches!(route.deployment.provider.as_str(), "QIANFAN_TOKEN_PLAN" | "QIANFAN")
                && !truncated
                && serde_json::from_slice::<Value>(&diagnostic)
                    .ok()
                    .and_then(|body| body.get("error")?.get("code")?.as_str().map(str::to_owned))
                    .as_deref() == Some("subscription_expired");
            // ARC's observed billing refusal has no generated output. Match only
            // its complete structured error, preserving other authorization failures.
            let arc_balance_exhausted = status.as_u16() == 402
                && route.deployment.provider == "ARC"
                && !truncated
                && serde_json::from_slice::<Value>(&diagnostic)
                    .ok()
                    .is_some_and(|body| {
                        let error = body.get("error").unwrap_or(&body);
                        error.get("code").and_then(Value::as_str) == Some("insufficient_balance")
                            && error.get("type").and_then(Value::as_str) == Some("billing_error")
                    });
            let fallback = (matches!(status.as_u16(), 429 | 500 | 502 | 503 | 504)
                || subscription_expired || arc_balance_exhausted) && index + 1 < chain.len();
            if fallback {
                life.event("fallback", json!({"attempt": index + 1, "http_status": status.as_u16(),
                    "elapsed_ms": attempt_started.elapsed().as_millis(),
                    "diagnostic": diagnostic_for_log(&diagnostic, &payload), "truncated": truncated,
                    "error_body_bytes": diagnostic.len(), "next_deployment": chain[index + 1].deployment.deployment_id}));
                continue;
            }
            life.event(
                "upstream_error",
                json!({"attempt": index + 1, "http_status": status.as_u16(),
                "elapsed_ms": attempt_started.elapsed().as_millis(),
                "diagnostic": diagnostic_for_log(&diagnostic, &payload), "truncated": truncated}),
            );
            life.committed = true;
            life.end("upstream_http_error");
            let mut output = Response::new(Body::from(diagnostic));
            *output.status_mut() = status;
            *output.headers_mut() = headers;
            if truncated {
                output.headers_mut().insert(
                    "x-model-proxy-error-truncated",
                    header::HeaderValue::from_static("true"),
                );
            }
            return output;
        }
        life.committed = true;
        life.event(
            "commit",
            json!({"attempt": index + 1, "http_status": status.as_u16(),
                   "elapsed_ms": attempt_started.elapsed().as_millis()}),
        );
        // Returning headers is the conservative commitment point, even before an
        // SSE data frame. No interpretation, continuation, or fallback follows it.
        let mut upstream = response.bytes_stream();
        let usage_channel = json!({"attempt": index + 1, "provider": route.deployment.provider,
            "plan": route.deployment.plan, "wire_model": route.deployment.wire_model});
        drop(payload);
        let stream = async_stream::stream! {
            let mut bytes = 0u64;
            let mut first = true;
            let mut usage = usage::Capture::new(requested_stream);
            loop {
                let read_deadline = deadline.min(Instant::now() + ms(app.config.limits.stream_idle_ms));
                match timeout_at(read_deadline, upstream.next()).await {
                    Ok(Some(Ok(chunk))) => {
                        if first { life.event("first_body_bytes", json!({"bytes": chunk.len()})); first = false; }
                        bytes += chunk.len() as u64;
                        usage.push(&chunk);
                        yield Ok::<_, io::Error>(chunk);
                    }
                    Ok(Some(Err(cause))) => {
                        life.event("usage", json!({"channel": usage_channel, "capture": usage.finish(false)}));
                        life.event("stream_error", json!({"diagnostic": transport_diagnostic(cause), "bytes": bytes}));
                        life.end("upstream_body_error");
                        yield Err(io::Error::other("upstream body failed after commit"));
                        break;
                    }
                    Ok(None) => {
                        life.event("usage", json!({"channel": usage_channel, "capture": usage.finish(true)}));
                        life.event("body_end", json!({"bytes": bytes})); life.end("complete"); break;
                    }
                    Err(_) => {
                        life.event("usage", json!({"channel": usage_channel, "capture": usage.finish(false)}));
                        life.end("stream_idle_or_total_timeout");
                        yield Err(io::Error::new(io::ErrorKind::TimedOut, "upstream body deadline"));
                        break;
                    }
                }
            }
        };
        let mut output = Response::new(Body::from_stream(stream));
        *output.status_mut() = status;
        *output.headers_mut() = headers;
        return output;
    }
    life.end("routes_exhausted");
    error(StatusCode::BAD_GATEWAY, "routes_exhausted")
}

fn diagnostic_for_log(bytes: &[u8], payload: &Value) -> String {
    fn redact(value: &Value, text: &mut String) {
        match value {
            Value::String(s) if !s.is_empty() => {
                *text = text.replace(s, "[request field]");
                let escaped = serde_json::to_string(s).unwrap_or_default();
                if escaped.len() > 2 {
                    *text = text.replace(&escaped[1..escaped.len() - 1], "[request field]");
                }
            }
            Value::Array(a) => {
                for v in a {
                    redact(v, text);
                }
            }
            Value::Object(o) => {
                for (k, v) in o {
                    if k != "model" {
                        redact(v, text);
                    }
                }
            }
            _ => {}
        }
    }
    let mut text = String::from_utf8_lossy(bytes).into_owned();
    redact(payload, &mut text);
    text
}

async fn read_error(response: reqwest::Response, deadline: Instant, app: &App) -> (Vec<u8>, bool) {
    let mut stream = response.bytes_stream();
    let mut bytes = Vec::new();
    let end = deadline.min(Instant::now() + Duration::from_secs(2));
    while bytes.len() < app.config.limits.error_bytes {
        match timeout_at(end, stream.next()).await {
            Ok(Some(Ok(chunk))) => bytes.extend_from_slice(
                &chunk[..chunk.len().min(app.config.limits.error_bytes - bytes.len())],
            ),
            Ok(None) => return (bytes, false),
            _ => return (bytes, true),
        }
    }
    (bytes, true)
}

async fn signal() {
    let mut terminate = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
        .expect("SIGTERM handler");
    tokio::select! { _ = terminate.recv() => {}, _ = tokio::signal::ctrl_c() => {} }
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    rustls::crypto::ring::default_provider()
        .install_default()
        .map_err(|_| "TLS crypto provider was already configured")?;
    let mut args = std::env::args().skip(1);
    let mut config_path = None;
    let mut credentials_path = None;
    while let Some(flag) = args.next() {
        match flag.as_str() {
            "--config" => config_path = args.next().map(PathBuf::from),
            "--credentials" => credentials_path = args.next().map(PathBuf::from),
            _ => {
                return Err(
                    "usage: factory26-model-proxy --config FILE --credentials PRIVATE_JSON".into(),
                );
            }
        }
    }
    let (config, routes, token, secrets, config_sha) = config::load(
        &config_path.ok_or("missing --config")?,
        &credentials_path.ok_or("missing --credentials")?,
    )?;
    let client = reqwest::Client::builder()
        .connect_timeout(ms(config.limits.connect_ms))
        .timeout(ms(config.limits.total_ms))
        .redirect(reqwest::redirect::Policy::none())
        .retry(reqwest::retry::never())
        .no_proxy()
        .http1_only()
        .pool_max_idle_per_host(0)
        .no_gzip()
        .no_brotli()
        .no_deflate()
        .no_zstd();
    // Reqwest's Linux default closes stalled uploads after 30s, before our
    // explicit request deadline. Keep the configured total deadline authoritative.
    #[cfg(any(target_os = "android", target_os = "fuchsia", target_os = "linux"))]
    let client = client.tcp_user_timeout(None);
    let client = client.build()?;
    let listener = TcpListener::bind(config.listen).await?;
    let app = Arc::new(App {
        config,
        routes,
        client,
        token,
        secrets,
        config_sha,
        next: AtomicU64::new(1),
    });
    let router = Router::new()
        .route("/health/liveliness", get(health))
        .route("/v1/chat/completions", post(chat))
        .with_state(app.clone());
    app.log(
        json!({"event": "ready", "listen": app.config.listen.to_string(),
        "catalog_sha256": app.config.catalog_sha256, "routes_sha256": app.config.routes_sha256,
        "version": env!("CARGO_PKG_VERSION")}),
    );
    let shutdown = CancellationToken::new();
    let mut tasks = JoinSet::new();
    let stopping = signal();
    tokio::pin!(stopping);
    loop {
        tokio::select! {
            biased;
            _ = &mut stopping => break,
            Some(result) = tasks.join_next(), if !tasks.is_empty() => {
                if let Err(cause) = result { app.log(json!({"event": "connection_task_error", "diagnostic": cause.to_string()})); }
            }
            accepted = listener.accept() => {
                let (socket, _) = accepted?;
                socket.set_nodelay(true)?;
                let router = router.clone();
                let app = app.clone();
                let shutdown = shutdown.clone();
                tasks.spawn(async move {
                    let mut builder = hyper::server::conn::http1::Builder::new();
                    builder.half_close(false).keep_alive(false).max_buf_size(16 * 1024)
                        .timer(TokioTimer::new()).header_read_timeout(ms(app.config.limits.body_ms));
                    let connection = builder.serve_connection(TokioIo::new(socket), TowerToHyperService::new(router));
                    tokio::pin!(connection);
                    let total = tokio::time::sleep(ms(app.config.limits.total_ms));
                    tokio::pin!(total);
                    tokio::select! {
                        result = &mut connection => {
                            if let Err(cause) = result { app.log(json!({"event": "connection_error", "diagnostic": cause.to_string()})); }
                        }
                        _ = &mut total => app.log(json!({"event": "connection_total_timeout"})),
                        _ = shutdown.cancelled() => {
                            connection.as_mut().graceful_shutdown();
                            tokio::select! { _ = &mut connection => {}, _ = &mut total => {} }
                        }
                    }
                });
            }
        }
    }
    drop(listener);
    app.log(json!({"event": "stopping", "connections": tasks.len()}));
    shutdown.cancel();
    if timeout(ms(app.config.limits.shutdown_ms), async {
        while tasks.join_next().await.is_some() {}
    })
    .await
    .is_err()
    {
        tasks.abort_all();
        while tasks.join_next().await.is_some() {}
        app.log(json!({"event": "shutdown_deadline"}));
    }
    app.log(json!({"event": "stopped"}));
    Ok(())
}
