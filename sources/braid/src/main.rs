mod agent_session;
mod cli;
mod config;
mod context;
mod evidence;
mod group;
mod health;
mod local;
mod objects;
mod provider;
mod queue;
mod store;
mod telemetry;
mod worktree;

fn main() {
    // OTel Rust 0.32 parses an explicit "none" as a compression algorithm and fails.
    // Re-exec before creating threads: clearing process-global env inside Tokio is unsafe.
    let unset: Vec<_> = ["", "_TRACES", "_LOGS", "_METRICS"]
        .into_iter()
        .map(|signal| format!("OTEL_EXPORTER_OTLP{signal}_COMPRESSION"))
        .filter(|name| std::env::var(name).is_ok_and(|value| value.is_empty() || value == "none"))
        .collect();
    if !unset.is_empty() {
        let mut command =
            std::process::Command::new(std::env::current_exe().expect("current executable"));
        command.args(std::env::args_os().skip(1));
        for name in unset {
            command.env_remove(name);
        }
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt as _;
            eprintln!("cannot normalize OTLP environment: {}", command.exec());
            std::process::exit(1);
        }
        #[cfg(not(unix))]
        {
            std::process::exit(
                command.status().expect("normalize OTLP environment").code().unwrap_or(1),
            );
        }
    }
    run();
}

#[tokio::main]
async fn run() {
    if let Err(error) = Box::pin(cli::run()).await {
        eprintln!("error: {error:#}");
        std::process::exit(1);
    }
}
