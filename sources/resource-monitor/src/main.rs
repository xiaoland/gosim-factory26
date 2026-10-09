mod sample;
use sample::{Sampler, clock, identity, read_values, save};
use serde_json::{Value, json};
use std::{
    fs,
    io::{self, BufRead, Read, Write},
    path::PathBuf,
    sync::mpsc,
    thread,
    time::{Duration, Instant},
};

fn events(v: &Value) -> std::collections::BTreeMap<String, u64> {
    let mut out = std::collections::BTreeMap::new();
    for name in ["memory.events", "pids.events"] {
        for line in v[name].as_str().unwrap_or("").lines() {
            let mut parts = line.split_whitespace();
            if let (Some(k), Some(n)) = (parts.next(), parts.next()) {
                if let Ok(n) = n.parse() {
                    out.insert(format!("{}.{k}", name.split('.').next().unwrap()), n);
                }
            }
        }
    }
    out
}
fn at_limit(v: &Value) -> bool {
    [
        ("memory.current", "memory.max"),
        ("pids.current", "pids.max"),
    ]
    .iter()
    .any(|(a, b)| {
        match (
            v[*a].as_str().and_then(|s| s.parse::<u64>().ok()),
            v[*b].as_str().and_then(|s| s.parse::<u64>().ok()),
        ) {
            (Some(a), Some(b)) => a >= b,
            _ => false,
        }
    })
}
fn failure(
    e: &std::collections::BTreeMap<String, u64>,
    base: &std::collections::BTreeMap<String, u64>,
) -> bool {
    ["memory.oom", "memory.oom_kill", "pids.max"]
        .iter()
        .any(|k| e.get(*k).zip(base.get(*k)).is_some_and(|(a, b)| a > b))
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let mut run = None;
    let mut root = unsafe { libc::getppid() };
    let mut only = false;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--run" => {
                i += 1;
                run = Some(PathBuf::from(args.get(i).ok_or("--run needs a path")?));
            }
            "--root-pid" => {
                i += 1;
                root = args.get(i).ok_or("--root-pid needs a PID")?.parse()?;
            }
            "--stdin-only" => only = true,
            _ => return Err(format!("unknown argument: {}", args[i]).into()),
        }
        i += 1;
    }
    let run =
        run.ok_or("usage: factory26-resource-monitor --run DIR --root-pid PID [--stdin-only]")?;
    if root <= 0 || (!only && root <= 1) {
        return Err("root PID must be greater than one".into());
    }
    fs::create_dir_all(run.join("process-evidence"))?;
    let mut sampler = Sampler::new(run.clone(), root)?;
    let cgroup = sampler.cgroup.clone();
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let mut input = io::stdin().lock();
        loop {
            let mut bytes = Vec::new();
            let n = input.by_ref().take(65537).read_until(b'\n', &mut bytes);
            match n {
                Ok(0) => break,
                Ok(_) if bytes.len() <= 65536 => match serde_json::from_slice::<Value>(&bytes) {
                    Ok(v) => {
                        if tx.send(v).is_err() {
                            return;
                        }
                    }
                    Err(e) => {
                        eprintln!("resource control JSON: {e}");
                        break;
                    }
                },
                Ok(_) => {
                    eprintln!("resource control exceeds 64 KiB");
                    break;
                }
                Err(e) => {
                    eprintln!("resource control read: {e}");
                    break;
                }
            }
        }
        let _ = tx.send(json!({"kind":"final"}));
    });
    // A single replaceable request keeps expensive /proc reads off the guard loop.
    let pending = std::sync::Arc::new((
        std::sync::Mutex::new((
            Some(
                json!({"kind":"baseline","kinds":["baseline"],"requested_monotonic_ns":clock(libc::CLOCK_MONOTONIC)}),
            ),
            false,
            0u64,
        )),
        std::sync::Condvar::new(),
    ));
    let worker_pending = pending.clone();
    let worker_run = run.clone();
    let (finished_tx, finished_rx) = mpsc::channel();
    thread::spawn(move || {
        loop {
            let (lock, cv) = &*worker_pending;
            let mut state = lock.lock().unwrap();
            while state.0.is_none() && !state.1 {
                state = cv.wait(state).unwrap();
            }
            let Some(mut request) = state.0.take() else {
                break;
            };
            request["coalesced_requests"] = json!(state.2);
            drop(state);
            let started = clock(libc::CLOCK_MONOTONIC);
            let result = sampler.sample(request["kind"].as_str().unwrap_or("sample"), &request);
            if let Err(ref e) = result {
                eprintln!("resource sample failed: {e}");
                let _ = save(
                    &worker_run.join("resource-sampler-error.json"),
                    &json!({"phase":request["kind"],"error":sample::error(e)}),
                );
            }
            if let Some(id) = request.get("request_id") {
                println!(
                    "{}",
                    json!({"request_id":id,"status":if result.is_ok(){"sampled"}else{"failed"},"error":result.as_ref().err().map(sample::error)})
                );
                let _ = io::stdout().flush();
            }
            let _ = save(
                &worker_run.join("resource-sampling-worker.json"),
                &json!({"kind":request["kind"],"requested_monotonic_ns":request["requested_monotonic_ns"],"started_monotonic_ns":started,"finished_monotonic_ns":clock(libc::CLOCK_MONOTONIC),"coalesced_requests":request["coalesced_requests"]}),
            );
        }
        let _ = finished_tx.send(());
    });
    let enqueue = |kind: &str, request_id: Option<&Value>| {
        let (lock, cv) = &*pending;
        let mut state = lock.lock().unwrap();
        let mut request = json!({"kind":kind,"kinds":[kind],"requested_monotonic_ns":clock(libc::CLOCK_MONOTONIC)});
        if let Some(id) = request_id {
            request["request_id"] = id.clone();
        }
        if let Some(old) = state.0.take() {
            state.2 += 1;
            request["requested_monotonic_ns"] = old["requested_monotonic_ns"].clone();
            let mut kinds = old["kinds"].as_array().cloned().unwrap_or_default();
            if !kinds.contains(&json!(kind)) {
                kinds.push(json!(kind));
            }
            request["kinds"] = json!(kinds);
            let priority = |kind: &str| match kind {
                "final" => 3,
                "resource_limit" => 2,
                "baseline" => 1,
                _ => 0,
            };
            if priority(kind) < priority(old["kind"].as_str().unwrap_or("sample")) {
                request["kind"] = old["kind"].clone();
            }
        }
        state.0 = Some(request);
        cv.notify_one();
    };
    let mut previous_events = events(&read_values(cgroup.as_deref()).0);
    println!(
        "{}",
        json!({"status":"ready","pid":std::process::id(),"language":"rust","cgroup_path":cgroup})
    );
    io::stdout().flush()?;

    let mut previous = clock(libc::CLOCK_MONOTONIC);
    let mut deadline = Instant::now() + Duration::from_secs(2);
    loop {
        match rx.recv_timeout(deadline.saturating_duration_since(Instant::now())) {
            Ok(command) => match command["kind"].as_str() {
                Some("register_entry") => {
                    let pid = command["pid"].as_i64().ok_or("entry PID missing")? as i32;
                    let current = identity(pid);
                    if pid <= 1
                        || current["ppid"].as_i64() != Some(root as i64)
                        || current["starttime"] != command["starttime"]
                    {
                        return Err("entry does not match direct owned child birth identity".into());
                    }
                    // Registration is evidence, never authority to terminate
                    // the generation entry and bypass its evaluation handoff.
                    save(&run.join("resource-entry.json"), &command)?;
                }
                Some("sample" | "baseline" | "resource_limit") => enqueue(
                    command["sample_kind"]
                        .as_str()
                        .unwrap_or(command["kind"].as_str().unwrap()),
                    command.get("request_id"),
                ),
                Some("final") => break,
                _ => return Err("unknown resource command".into()),
            },
            Err(mpsc::RecvTimeoutError::Disconnected) => break,
            Err(mpsc::RecvTimeoutError::Timeout) => {}
        }
        if Instant::now() < deadline {
            continue;
        }
        deadline = Instant::now() + Duration::from_secs(2);
        if only {
            continue;
        }
        let started = clock(libc::CLOCK_MONOTONIC);
        let (values, errors) = read_values(cgroup.as_deref());
        let ev = events(&values);
        let current_limit = at_limit(&values);
        let new_event = failure(&ev, &previous_events);
        previous_events = ev.clone();
        let limited = current_limit || new_event;
        let row = json!({"observed_at_ns":clock(libc::CLOCK_REALTIME),"check_monotonic_ns":started,"actual_interval_ns":started-previous,"scheduling_delay_ns":(started-previous).saturating_sub(2_000_000_000),"cgroup_path":cgroup,"values":values,"errors":errors});
        previous = started;
        enqueue(if limited { "resource_limit" } else { "sample" }, None);
        save(&run.join("resource-observation.json"), &row)?;
        if !limited {
            continue;
        }
        let reclaim = cgroup
            .as_ref()
            .filter(|_| current_limit)
            .map(|p| fs::write(p.join("memory.reclaim"), "268435456"));
        thread::sleep(Duration::from_secs(1));
        let (after, errors) = read_values(cgroup.as_deref());
        let still = at_limit(&after);
        let after_events = events(&after);
        let additional_event = failure(&after_events, &previous_events);
        previous_events = after_events;
        let action = json!({"status":if still {"resource_exhausted"} else if errors.as_object().is_some_and(|errors| !errors.is_empty()) {"unknown"} else {"limit_not_observed"},"new_resource_event":new_event,"additional_resource_event":additional_event,"entry_action":"none_observation_only","trigger":row,"after":{"values":after,"errors":errors},"memory_reclaim":match reclaim {Some(Ok(()))=>json!("requested"),Some(Err(e))=>sample::error(&e),None=>json!("unavailable")}});
        save(&run.join("resource-remediation.json"), &action)?;
        if still {
            let failed = json!({"status":"resource_exhausted","reason":"memory_or_pids_limit_observed_after_reclaim","entry_action":"none_observation_only","remediation":action});
            save(&run.join("resource-exhausted.json"), &failed)?;
        }
    }
    enqueue("final", None);
    {
        let (lock, cv) = &*pending;
        lock.lock().unwrap().1 = true;
        cv.notify_one();
    }
    if finished_rx.recv_timeout(Duration::from_secs(3)).is_err() {
        save(
            &run.join("resource-sampler-error.json"),
            &json!({"phase":"close","status":"incomplete","reason":"sampler_did_not_finish_within_shutdown_window"}),
        )?;
        return Err("final resource sample incomplete".into());
    }
    Ok(())
}
