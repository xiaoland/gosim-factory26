use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet, VecDeque},
    fs::{self, OpenOptions},
    io::{self, Write},
    os::unix::{fs::MetadataExt, io::AsRawFd},
    path::{Path, PathBuf},
};
const M: u64 = 1024 * 1024;
const FILES: &[&str] = &[
    "memory.events",
    "memory.events.local",
    "memory.current",
    "memory.peak",
    "memory.stat",
    "memory.pressure",
    "memory.max",
    "memory.oom.group",
    "memory.swap.current",
    "memory.swap.peak",
    "memory.swap.max",
    "pids.current",
    "pids.max",
    "pids.events",
    "cpu.stat",
    "cpu.pressure",
    "io.stat",
    "io.pressure",
];
pub fn clock(id: libc::clockid_t) -> u64 {
    let mut t = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    unsafe { libc::clock_gettime(id, &mut t) };
    t.tv_sec as u64 * 1_000_000_000 + t.tv_nsec as u64
}
fn stamp() -> Value {
    json!({"realtime_ns":clock(libc::CLOCK_REALTIME),"monotonic_ns":clock(libc::CLOCK_MONOTONIC)})
}
pub fn error(e: &io::Error) -> Value {
    json!({"type":"IOError","errno":e.raw_os_error(),"message":e.to_string()})
}
pub fn save(p: &Path, v: &Value) -> io::Result<()> {
    if let Some(parent) = p.parent() {
        fs::create_dir_all(parent)?;
    }
    let tmp = p.with_extension(format!("{}.tmp", std::process::id()));
    let mut f = OpenOptions::new()
        .create(true)
        .truncate(true)
        .write(true)
        .open(&tmp)?;
    serde_json::to_writer(&mut f, v)?;
    f.write_all(b"\n")?;
    f.sync_all()?;
    fs::rename(tmp, p)
}
fn read(p: &Path, r: &mut Value, key: &str) {
    match fs::read_to_string(p) {
        Ok(v) => r[key] = json!(v.trim()),
        Err(e) => r["errors"][key] = error(&e),
    }
}
fn stat(pid: i32) -> io::Result<Vec<String>> {
    let s = fs::read_to_string(format!("/proc/{pid}/stat"))?;
    let tail = s
        .rsplit_once(')')
        .ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                "process stat has no closing parenthesis",
            )
        })?
        .1;
    let fields: Vec<_> = tail.split_whitespace().map(String::from).collect();
    if fields.len() < 22 {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "process stat truncated",
        ));
    }
    for i in [1, 2, 11, 12, 19, 21] {
        fields[i]
            .parse::<i64>()
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))?;
    }
    Ok(fields)
}
fn n(fields: &[String], i: usize) -> i64 {
    fields[i].parse().unwrap_or(0)
}
pub fn identity(pid: i32) -> Value {
    let mut r = json!({"pid":pid,"errors":{}});
    let root = PathBuf::from(format!("/proc/{pid}"));
    match stat(pid) {
        Ok(f) => {
            r["ppid"] = json!(n(&f, 1));
            r["pgid"] = json!(n(&f, 2));
            r["starttime"] = json!(n(&f, 19));
            r["state"] = json!(f[0]);
            r["rss_pages"] = json!(n(&f, 21));
        }
        Err(e) => r["errors"]["stat"] = error(&e),
    }
    for k in ["comm", "cgroup"] {
        read(&root.join(k), &mut r, k);
    }
    match fs::read_to_string(root.join("status")) {
        Ok(s) => {
            r["status"] = json!({});
            for line in s.lines() {
                if let Some((k, v)) = line.split_once(':') {
                    if [
                        "Tgid", "Pid", "PPid", "NSpid", "Threads", "VmRSS", "VmHWM", "VmSize",
                        "RssAnon", "RssFile", "RssShmem", "VmSwap", "CapEff",
                    ]
                    .contains(&k)
                    {
                        r["status"][k] = json!(v.trim());
                    }
                }
            }
        }
        Err(e) => r["errors"]["status"] = error(&e),
    }
    for k in ["exe", "cwd", "ns/pid", "ns/cgroup"] {
        match fs::read_link(root.join(k)) {
            Ok(p) => r[k] = json!(p.to_string_lossy()),
            Err(e) => r["errors"][k] = error(&e),
        }
    }
    r
}
fn unescape(s: &str) -> String {
    let b = s.as_bytes();
    let mut out = Vec::new();
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'\\'
            && i + 3 < b.len()
            && b[i + 1..i + 4].iter().all(|v| (b'0'..=b'7').contains(v))
        {
            out.push((b[i + 1] - b'0') * 64 + (b[i + 2] - b'0') * 8 + b[i + 3] - b'0');
            i += 4;
        } else {
            out.push(b[i]);
            i += 1;
        }
    }
    String::from_utf8_lossy(&out).into_owned()
}
fn cgroup() -> Option<PathBuf> {
    let cg = fs::read_to_string("/proc/self/cgroup").ok()?;
    let membership = cg.lines().find_map(|l| l.strip_prefix("0::"))?;
    for line in fs::read_to_string("/proc/self/mountinfo").ok()?.lines() {
        let Some((before, after)) = line.split_once(" - ") else {
            continue;
        };
        if after.split_whitespace().next() != Some("cgroup2") {
            continue;
        }
        let f: Vec<_> = before.split_whitespace().collect();
        if f.len() < 5 {
            continue;
        }
        let mount = PathBuf::from(unescape(f[4]));
        let root = PathBuf::from(unescape(f[3]));
        if membership == "/" {
            return Some(mount);
        }
        if let Ok(tail) = Path::new(membership).strip_prefix(root) {
            return Some(mount.join(tail));
        }
    }
    None
}
pub fn read_values(cg: Option<&Path>) -> (Value, Value) {
    let mut values = json!({});
    let mut errors = json!({});
    if let Some(cg) = cg {
        for k in FILES {
            match fs::read_to_string(cg.join(k)) {
                Ok(s) => values[*k] = json!(s.trim()),
                Err(e) => errors[*k] = error(&e),
            }
        }
    } else {
        errors["cgroup"] = json!({"message":"cgroup v2 not visible"});
    }
    (values, errors)
}
fn append(run: &Path, name: &str, row: &Value, cap: u64) -> io::Result<bool> {
    let folder = run.join("process-evidence");
    fs::create_dir_all(&folder)?;
    let p = folder.join(name);
    let marker = folder.join(format!("{name}.capped.json"));
    let mut f = OpenOptions::new().create(true).append(true).open(&p)?;
    if unsafe { libc::flock(f.as_raw_fd(), libc::LOCK_EX) } != 0 {
        return Err(io::Error::last_os_error());
    }
    if marker.exists() {
        return Ok(false);
    }
    let mut v = row.clone();
    v["schema_version"] = json!(1);
    let time = stamp();
    v["realtime_ns"] = time["realtime_ns"].clone();
    v["monotonic_ns"] = time["monotonic_ns"].clone();
    let mut encoded = serde_json::to_vec(&v)?;
    encoded.push(b'\n');
    let size = f.metadata()?.len();
    let success = size + encoded.len() as u64 <= cap - 4096;
    if !success {
        let mark = json!({"kind":"log_capped","cap_bytes":cap,"bytes_before":size,"dropped_kind":row["kind"]});
        save(&marker, &mark)?;
        encoded = serde_json::to_vec(&mark)?;
        encoded.push(b'\n');
    }
    f.write_all(&encoded)?;
    f.sync_all()?;
    Ok(success)
}
#[derive(Clone)]
struct Proc {
    pid: i32,
    ppid: i32,
    birth: i64,
    state: String,
    rss: i64,
    scope: usize,
    depth: usize,
    record: Value,
}
pub struct Sampler {
    run: PathBuf,
    pub cgroup: Option<PathBuf>,
    root: i32,
    root_birth: Value,
    boot: String,
    membership: String,
    last_sample: Option<u64>,
    last_detail: u64,
    attempts: BTreeMap<(i32, i64), u64>,
    success: BTreeMap<(i32, i64), u64>,
    previous: BTreeSet<(i32, i64)>,
    previous_values: Value,
    recent: VecDeque<Value>,
    samples: u64,
    rotations: u64,
    incidents_dropped: u64,
    segment_started: Option<u64>,
    previous_started: Option<u64>,
}
impl Sampler {
    pub fn new(run: PathBuf, root: i32) -> io::Result<Self> {
        let root_birth = identity(root)["starttime"].clone();
        let cg = cgroup();
        let boot = fs::read_to_string("/proc/sys/kernel/random/boot_id")?
            .trim()
            .to_string();
        let membership = fs::read_to_string("/proc/self/cgroup")?.trim().to_string();
        append(
            &run,
            "resources-baseline.jsonl",
            &json!({"kind":"capabilities","collector":identity(std::process::id() as i32),"language":"rust","cgroup_path":cg,"cgroup_mapping":if cg.is_some(){"visible-cgroup-v2"}else{"unavailable"},"root_pid":root,"root_process":identity(root),"interval_seconds":2,"memory_detail_interval_seconds":10,"max_memory_detail_processes":12,"max_processes_per_sample":256,"page_size":unsafe{libc::sysconf(libc::_SC_PAGESIZE)},"clock_ticks":unsafe{libc::sysconf(libc::_SC_CLK_TCK)},"segment_bytes":31*M,"cap_bytes":96*M,"incident_cap_bytes":16*M,"critical_cap_bytes":16*M,"raw":{"/proc/self/cgroup":membership,"/proc/sys/kernel/random/boot_id":boot}}),
            2 * M,
        )?;
        Ok(Self {
            run,
            cgroup: cg,
            root,
            root_birth,
            boot,
            membership,
            last_sample: None,
            last_detail: 0,
            attempts: BTreeMap::new(),
            success: BTreeMap::new(),
            previous: BTreeSet::new(),
            previous_values: json!({}),
            recent: VecDeque::new(),
            samples: 0,
            rotations: 0,
            incidents_dropped: 0,
            segment_started: None,
            previous_started: None,
        })
    }
    pub fn sample(&mut self, kind: &str, request: &Value) -> io::Result<()> {
        let cpu = clock(libc::CLOCK_THREAD_CPUTIME_ID);
        let begin = stamp();
        let now = begin["monotonic_ns"].as_u64().unwrap();
        let (values, errors) = read_values(self.cgroup.as_deref());
        let mut row = json!({"kind":kind,"cgroup_path":self.cgroup,"values":values,"errors":errors,"processes":[],"process_limit":256,"processes_omitted":0,"visible_processes":0,"sample_started":begin,"boot_id":self.boot,"scope_counts":{},"scope_omitted":{},"classification_errors":[],"classification_errors_omitted":0,"process_totals":{},"memory_detail":[],"scheduling":request});
        row["scheduling"]["queue_delay_ns"] =
            json!(now.saturating_sub(request["requested_monotonic_ns"].as_u64().unwrap_or(now)));
        if let Some(cg) = &self.cgroup {
            match cg.metadata() {
                Ok(m) => row["cgroup_identity"] = json!({"device":m.dev(),"inode":m.ino()}),
                Err(e) => row["errors"]["cgroup_identity"] = error(&e),
            }
        }
        let mut procs = BTreeMap::new();
        for entry in fs::read_dir("/proc")? {
            let entry = entry?;
            let Ok(pid) = entry.file_name().to_string_lossy().parse::<i32>() else {
                continue;
            };
            let mut p = identity(pid);
            let started = stamp();
            let f = match stat(pid) {
                Ok(fields) => fields,
                Err(e) => {
                    let errors = row["classification_errors"].as_array_mut().unwrap();
                    if errors.len() < 32 {
                        errors.push(json!({"pid":pid,"field":"stat","error":error(&e)}));
                    } else {
                        row["classification_errors_omitted"] =
                            json!(row["classification_errors_omitted"].as_u64().unwrap() + 1);
                    }
                    continue;
                }
            };
            p["cpu_ticks"] = json!(n(&f, 11) + n(&f, 12));
            p["counter_read_started"] = started;
            p["counter_errors"] = json!({});
            let birth = n(&f, 19);
            let matched = p["starttime"].as_i64() == Some(birth);
            p["counter_identity_matches"] = json!(matched);
            if !matched {
                p.as_object_mut().unwrap().remove("cpu_ticks");
            }
            match fs::read_to_string(entry.path().join("io")) {
                Ok(s) => {
                    let io: BTreeMap<_, _> = s
                        .lines()
                        .filter_map(|l| {
                            let (k, v) = l.split_once(':')?;
                            Some((k, v.trim().parse::<u64>().ok()?))
                        })
                        .collect();
                    if matched {
                        p["io_bytes"] = json!(io);
                    }
                }
                Err(e) => p["counter_errors"]["io"] = error(&e),
            }
            procs.insert(
                pid,
                Proc {
                    pid,
                    ppid: n(&f, 1) as i32,
                    birth,
                    state: f[0].clone(),
                    rss: n(&f, 21),
                    scope: 3,
                    depth: 0,
                    record: p,
                },
            );
        }
        row["visible_processes"] = json!(procs.len());
        let root_matches = procs
            .get(&self.root)
            .is_some_and(|p| json!(p.birth) == self.root_birth);
        let snapshot = procs.clone();
        for p in procs.values_mut() {
            let mut parent = p.pid;
            let mut seen = BTreeSet::new();
            let mut depth = 0;
            while parent != self.root && seen.insert(parent) {
                let Some(next) = snapshot.get(&parent) else {
                    break;
                };
                parent = next.ppid;
                depth += 1;
            }
            p.scope = if root_matches && parent == self.root {
                0
            } else if p.record["cwd"]
                .as_str()
                .is_some_and(|s| Path::new(s).starts_with(&self.run))
            {
                1
            } else if p.record["cgroup"].as_str() == Some(self.membership.as_str()) {
                2
            } else {
                3
            };
            p.depth = depth;
        }
        let names = ["run-tree", "run-cwd", "current-cgroup", "other-visible"];
        let mut ranked: Vec<_> = procs.values().cloned().collect();
        ranked.sort_by_key(|p| {
            (
                matches!(p.state.as_str(), "Z" | "X"),
                p.scope,
                if p.scope == 0 { p.depth } else { 0 },
                -p.rss,
                p.pid,
            )
        });
        let mut counts = [0u64; 4];
        let mut omissions = [0u64; 4];
        let mut live = [0u64; 4];
        let mut dead = [0u64; 4];
        let mut rss = [0i64; 4];
        for (i, p) in ranked.iter().enumerate() {
            counts[p.scope] += 1;
            rss[p.scope] += p.rss;
            if matches!(p.state.as_str(), "Z" | "X") {
                dead[p.scope] += 1
            } else {
                live[p.scope] += 1
            };
            if i < 256 {
                let mut v = p.record.clone();
                v["sampling_scope"] = json!(names[p.scope]);
                v["tree_depth"] = if p.scope == 0 {
                    json!(p.depth)
                } else {
                    Value::Null
                };
                row["processes"].as_array_mut().unwrap().push(v);
            } else {
                omissions[p.scope] += 1;
            }
        }
        for i in 0..4 {
            row["scope_counts"][names[i]] = json!(counts[i]);
            row["scope_omitted"][names[i]] = json!(omissions[i]);
            row["process_totals"][names[i]] =
                json!({"live":live[i],"zombie_or_dead":dead[i],"rss_pages":rss[i]});
        }
        row["processes_omitted"] = json!(ranked.len().saturating_sub(256));
        let mut eligible: Vec<_> = ranked
            .iter()
            .filter(|p| !matches!(p.state.as_str(), "Z" | "X"))
            .collect();
        let births: BTreeSet<_> = eligible.iter().map(|p| (p.pid, p.birth)).collect();
        let started: Vec<_> = births
            .difference(&self.previous)
            .map(|(p, b)| json!({"pid":p,"starttime":b}))
            .collect();
        let vanished: Vec<_> = self
            .previous
            .difference(&births)
            .map(|(p, b)| json!({"pid":p,"starttime":b}))
            .collect();
        let mut reasons: Vec<String> = Vec::new();
        if ["baseline", "resource_limit", "final"].contains(&kind) {
            reasons.push(kind.into());
        }
        if !started.is_empty() {
            reasons.push("process_start".into());
        }
        if !vanished.is_empty() {
            reasons.push("process_disappearance".into());
        }
        for (file, reason) in [
            ("memory.current", "memory_growth"),
            ("memory.peak", "memory_peak_growth"),
        ] {
            if row["values"][file]
                .as_str()
                .and_then(|v| v.parse::<u64>().ok())
                .zip(
                    self.previous_values[file]
                        .as_str()
                        .and_then(|v| v.parse::<u64>().ok()),
                )
                .is_some_and(|(a, b)| a.saturating_sub(b) >= 64 * M)
            {
                reasons.push(reason.into());
            }
        }
        for k in ["memory.events.local", "pids.events"] {
            if !self.previous_values[k].is_null() && self.previous_values[k] != row["values"][k] {
                reasons.push(k.into());
            }
        }
        if now.saturating_sub(self.last_detail) >= 10_000_000_000 {
            reasons.push("periodic".into());
        }
        for k in request["kinds"]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
        {
            if k != "sample" && !reasons.iter().any(|v| v == k) {
                reasons.push(k.into());
            }
        }
        if !reasons.is_empty() {
            eligible.sort_by_key(|p| (p.scope, -p.rss, p.pid));
            let mut selected: Vec<_> = eligible.iter().take(6).copied().collect();
            let top: BTreeSet<_> = selected.iter().map(|p| p.pid).collect();
            let mut others: Vec<_> = eligible
                .iter()
                .filter(|p| !top.contains(&p.pid))
                .copied()
                .collect();
            others.sort_by_key(|p| {
                (
                    self.attempts.get(&(p.pid, p.birth)).copied().unwrap_or(0),
                    p.pid,
                )
            });
            selected.extend(others.into_iter().take(12 - selected.len()));
            for p in selected {
                let mut detail = json!({"pid":p.pid,"starttime":p.birth,"errors":{},"sampling_scope":names[p.scope],"observed_at":stamp()});
                let dir = PathBuf::from(format!("/proc/{}", p.pid));
                for name in ["smaps_rollup", "io"] {
                    match fs::read_to_string(dir.join(name)) {
                        Ok(s) => detail[name] = json!(s),
                        Err(e) => detail["errors"][name] = error(&e),
                    }
                }
                let mut fd = BTreeMap::from([
                    ("file", 0u64),
                    ("socket", 0),
                    ("pipe", 0),
                    ("anon_inode", 0),
                    ("other", 0),
                ]);
                match fs::read_dir(dir.join("fd")) {
                    Ok(entries) => {
                        for entry in entries {
                            match entry.and_then(|e| fs::read_link(e.path())) {
                                Ok(target) => {
                                    let s = target.to_string_lossy();
                                    let k = if s.starts_with('/') {
                                        "file"
                                    } else if s.starts_with("socket:") {
                                        "socket"
                                    } else if s.starts_with("pipe:") {
                                        "pipe"
                                    } else if s.starts_with("anon_inode:") {
                                        "anon_inode"
                                    } else {
                                        "other"
                                    };
                                    *fd.get_mut(k).unwrap() += 1;
                                }
                                Err(e) => detail["errors"]["fd_entry"] = error(&e),
                            }
                        }
                    }
                    Err(e) => detail["errors"]["fd"] = error(&e),
                }
                detail["file_descriptors"] = json!(fd);
                let same = identity(p.pid)["starttime"].as_i64() == Some(p.birth);
                detail["identity_matches"] = json!(same);
                if !same {
                    detail["errors"]["identity"] =
                        json!({"message":"process disappeared or PID reused during memory read"});
                }
                self.attempts.insert((p.pid, p.birth), now);
                if same && detail["smaps_rollup"].is_string() {
                    self.success.insert(
                        (p.pid, p.birth),
                        detail["observed_at"]["monotonic_ns"].as_u64().unwrap(),
                    );
                }
                row["memory_detail"].as_array_mut().unwrap().push(detail);
            }
            self.last_detail = now;
        }
        self.attempts.retain(|k, _| births.contains(k));
        self.success.retain(|k, _| births.contains(k));
        let attempted = row["memory_detail"].as_array().unwrap().len();
        let successful = row["memory_detail"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|d| d["identity_matches"] == true && d["smaps_rollup"].is_string())
            .count();
        row["memory_detail_coverage"] = json!({"eligible":eligible.len(),"attempted":attempted,"successful":successful,"not_attempted":eligible.len()-attempted,"selection":"six-largest-by-scope-plus-oldest-attempt","last_attempts":births.iter().take(256).map(|(p,b)|json!({"pid":p,"starttime":b,"monotonic_ns":self.attempts.get(&(*p,*b)),"last_success_monotonic_ns":self.success.get(&(*p,*b))})).collect::<Vec<_>>(),"freshness_entries_omitted":births.len().saturating_sub(256)});
        row["process_changes"] = json!({"started":started,"no_longer_visible":vanished});
        row["resource_event_reasons"] = json!(reasons);
        self.previous = births;
        self.previous_values = row["values"].clone();
        row["sample_finished"] = stamp();
        let finished = row["sample_finished"]["monotonic_ns"].as_u64().unwrap();
        row["collection_duration_ns"] = json!(finished - now);
        row["actual_interval_ns"] = json!(self.last_sample.map(|t| now - t));
        self.last_sample = Some(now);
        let mut usage = unsafe { std::mem::zeroed::<libc::rusage>() };
        unsafe { libc::getrusage(libc::RUSAGE_SELF, &mut usage) };
        let collector_identity = identity(std::process::id() as i32);
        let own_peak = collector_identity["status"]["VmHWM"]
            .as_str()
            .and_then(|s| s.split_whitespace().next())
            .and_then(|s| s.parse::<u64>().ok());
        row["collector"] = json!({"pid":std::process::id(),"language":"rust",
            "sampling_thread_cpu_ns":clock(libc::CLOCK_THREAD_CPUTIME_ID)-cpu,
            "process_peak_rss":own_peak,"process_peak_rss_unit":"KiB",
            "process_peak_rss_source":"proc-status-VmHWM",
            "getrusage_peak_rss":usage.ru_maxrss,
            "getrusage_peak_rss_unit":if cfg!(target_os="macos"){"bytes"}else{"KiB"}});
        if reasons.iter().any(|r| r != "periodic") {
            let critical = reasons.iter().any(|r| {
                [
                    "resource_limit",
                    "final",
                    "memory.events.local",
                    "pids.events",
                ]
                .contains(&r.as_str())
            });
            if !append(
                &self.run,
                if critical {
                    "resource-critical.jsonl"
                } else {
                    "resource-incidents.jsonl"
                },
                &json!({"kind":"resource_incident","preceding_samples":self.recent,"sample":row}),
                16 * M,
            )? {
                self.incidents_dropped += 1;
            }
        }
        if self.recent.len() == 3 {
            self.recent.pop_front();
        }
        self.recent.push_back(row.clone());
        let written = if kind == "baseline" {
            append(&self.run, "resources-baseline.jsonl", &row, 2 * M)?
        } else {
            let folder = self.run.join("process-evidence");
            let path = folder.join("resources.jsonl");
            let previous = folder.join("resources.previous.jsonl");
            let marker = folder.join("resources.jsonl.capped.json");
            if path.exists()
                && (path.metadata()?.len() + serde_json::to_vec(&row)?.len() as u64 + 256
                    > 31 * M - 4096
                    || marker.exists())
            {
                let discarded = previous.metadata().map(|m| m.len()).unwrap_or(0);
                let size = path.metadata()?.len();
                fs::rename(&path, &previous)?;
                if marker.exists() {
                    fs::remove_file(&marker)?;
                }
                self.rotations += 1;
                self.previous_started = self.segment_started;
                self.segment_started = None;
                append(
                    &self.run,
                    "resources.jsonl",
                    &json!({"kind":"resource_rotation","rotation":self.rotations,"previous_bytes":size,"discarded_previous_bytes":discarded,"previous_started_monotonic_ns":self.previous_started,"discarded_before_monotonic_ns":self.previous_started}),
                    31 * M,
                )?;
            }
            if self.segment_started.is_none() {
                self.segment_started = Some(now);
            }
            append(&self.run, "resources.jsonl", &row, 31 * M)?
        };
        let mut latest = json!({});
        for k in [
            "sample_started",
            "sample_finished",
            "collection_duration_ns",
            "actual_interval_ns",
            "cgroup_path",
            "cgroup_identity",
            "values",
            "errors",
        ] {
            latest[k] = row[k].clone();
        }
        save(
            &self.run.join("process-evidence/resource-latest.json"),
            &latest,
        )?;
        self.samples += 1;
        let folder = self.run.join("process-evidence");
        save(
            &folder.join("resource-status.json"),
            &json!({"kind":"resource_status","samples":self.samples,"last_sample_kind":kind,"language":"rust","write_succeeded":written,"capped":folder.join("resources.jsonl.capped.json").exists(),"incident_capped":folder.join("resource-incidents.jsonl.capped.json").exists(),"critical_capped":folder.join("resource-critical.jsonl.capped.json").exists(),"incidents_dropped":self.incidents_dropped,"cgroup_mapping":if self.cgroup.is_some(){"visible-cgroup-v2"}else{"unavailable"},"processes_omitted":row["processes_omitted"],"errors":row["errors"],"scope_counts":row["scope_counts"],"scope_omitted":row["scope_omitted"],"rotations":self.rotations,"segment_bytes":31*M,"total_duration_ns":clock(libc::CLOCK_MONOTONIC)-now,"collector_thread_cpu_ns":clock(libc::CLOCK_THREAD_CPUTIME_ID)-cpu,"collection_duration_ns":finished-now,"actual_interval_ns":row["actual_interval_ns"]}),
        )
    }
}
