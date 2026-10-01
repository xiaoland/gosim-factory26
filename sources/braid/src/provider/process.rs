#![allow(clippy::wildcard_imports)]
use super::*;
use std::sync::atomic::AtomicBool;

#[cfg(unix)]
const SIGKILL: i32 = 9;
#[cfg(unix)]
const SIGTERM: i32 = 15;

#[cfg(unix)]
pub(super) fn signal_process_group(pid: u32, signal: i32) -> std::io::Result<()> {
    // The app-server may create native workers of its own.  A dedicated
    // process group lets teardown fence the complete physical tree.
    let signal = format!("-{signal}");
    let group = format!("-{pid}");
    let status = std::process::Command::new("kill")
        .args([signal.as_str(), "--", group.as_str()])
        .stderr(Stdio::null())
        .status()?;
    if status.success() {
        Ok(())
    } else {
        Err(std::io::Error::other(format!("kill exited with {status}")))
    }
}

#[cfg(unix)]
pub(super) fn process_group_exists(pid: u32) -> bool {
    let group = format!("-{pid}");
    std::process::Command::new("kill")
        .args(["-0", "--", group.as_str()])
        .stderr(Stdio::null())
        .status()
        .is_ok_and(|status| status.success())
}

#[cfg(unix)]
pub(super) fn descendant_processes(root: u32) -> std::io::Result<Vec<u32>> {
    let output = std::process::Command::new("ps").args(["-axo", "pid=,ppid="]).output()?;
    if !output.status.success() {
        return Err(std::io::Error::other(format!("ps exited with {}", output.status)));
    }
    let rows: Vec<(u32, u32)> = String::from_utf8_lossy(&output.stdout)
        .lines()
        .filter_map(|line| {
            let mut fields = line.split_whitespace();
            Some((fields.next()?.parse().ok()?, fields.next()?.parse().ok()?))
        })
        .collect();
    let mut parents = vec![root];
    let mut descendants = Vec::new();
    while let Some(parent) = parents.pop() {
        for &(pid, ppid) in &rows {
            if ppid == parent && !descendants.contains(&pid) {
                descendants.push(pid);
                parents.push(pid);
            }
        }
    }
    Ok(descendants)
}

#[cfg(unix)]
pub(super) fn signal_processes(pids: &[u32], signal: i32) {
    for pid in pids.iter().rev() {
        let _ = std::process::Command::new("kill")
            .args([format!("-{signal}"), pid.to_string()])
            .stderr(Stdio::null())
            .status();
    }
}

#[cfg(unix)]
pub(super) fn any_process_exists(pids: &[u32]) -> bool {
    pids.iter().any(|pid| {
        std::process::Command::new("kill")
            .args(["-0", &pid.to_string()])
            .stderr(Stdio::null())
            .status()
            .is_ok_and(|status| status.success())
    })
}

pub(super) struct NativeProcess {
    child: StdMutex<Option<Child>>,
    teardown_failed: AtomicBool,
    stopping: Mutex<()>,
}

impl Drop for NativeProcess {
    fn drop(&mut self) {
        if let Some(child) =
            self.child.lock().unwrap_or_else(std::sync::PoisonError::into_inner).as_mut()
        {
            let _ = child.start_kill();
        }
    }
}

impl NativeProcess {
    pub(super) fn new(child: Child) -> Self {
        Self {
            child: StdMutex::new(Some(child)),
            teardown_failed: AtomicBool::new(false),
            stopping: Mutex::new(()),
        }
    }
    pub(super) async fn stop(&self, graceful: bool) -> Result<(), ProviderError> {
        let _stopping = self.stopping.lock().await;
        if self.teardown_failed.load(Ordering::Acquire) {
            return Err(ProviderError::Protocol(
                "native teardown previously failed; process state is unknown".into(),
            ));
        }
        let child = self.child.lock().unwrap_or_else(std::sync::PoisonError::into_inner).take();
        let Some(mut child) = child else { return Ok(()) };
        #[cfg(unix)]
        let pid = child.id();
        #[cfg(unix)]
        let descendants = pid
            .map(descendant_processes)
            .transpose()
            .map_err(|error| {
                self.teardown_failed.store(true, Ordering::Release);
                ProviderError::Protocol(error.to_string())
            })?
            .unwrap_or_default();
        // Bub owns graceful shutdown on stdin EOF; Codex retains its existing
        // immediate process-group termination behavior.
        let exited =
            graceful && matches!(timeout(Duration::from_secs(5), child.wait()).await, Ok(Ok(_)));
        #[cfg(unix)]
        if let Some(pid) = pid {
            if !exited {
                signal_processes(&descendants, SIGTERM);
            }
            if !exited && process_group_exists(pid) {
                if let Err(error) = signal_process_group(pid, SIGTERM) {
                    self.child
                        .lock()
                        .unwrap_or_else(std::sync::PoisonError::into_inner)
                        .replace(child);
                    return Err(ProviderError::Protocol(error.to_string()));
                }
            }
        }
        #[cfg(not(unix))]
        if !exited {
            child.start_kill().map_err(|error| ProviderError::Protocol(error.to_string()))?;
        }
        let waited = timeout(Duration::from_secs(180), child.wait()).await;
        match waited {
            Ok(Ok(_)) => {}
            Ok(Err(error)) => {
                self.child.lock().unwrap_or_else(std::sync::PoisonError::into_inner).replace(child);
                return Err(ProviderError::Protocol(error.to_string()));
            }
            Err(_) => {
                #[cfg(unix)]
                if let Some(pid) = pid {
                    let _ = signal_process_group(pid, SIGKILL);
                    let _ = timeout(Duration::from_secs(5), child.wait()).await;
                }
                self.teardown_failed.store(true, Ordering::Release);
                return Err(ProviderError::Timeout { method: "native teardown".into() });
            }
        }
        #[cfg(unix)]
        if let Some(pid) = pid {
            // The leader can exit before descendants do; reap the rest of its
            // dedicated group after the leader has been observed stopped.
            if process_group_exists(pid) {
                if let Err(error) = signal_process_group(pid, SIGKILL) {
                    self.teardown_failed.store(true, Ordering::Release);
                    return Err(ProviderError::Protocol(error.to_string()));
                }
                let deadline = tokio::time::Instant::now() + Duration::from_secs(5);
                while process_group_exists(pid) {
                    if tokio::time::Instant::now() >= deadline {
                        self.teardown_failed.store(true, Ordering::Release);
                        return Err(ProviderError::Protocol(
                            "native process group remained alive after SIGKILL".into(),
                        ));
                    }
                    tokio::time::sleep(Duration::from_millis(20)).await;
                }
            }
            signal_processes(&descendants, SIGKILL);
            let deadline = tokio::time::Instant::now() + Duration::from_secs(5);
            while any_process_exists(&descendants) {
                if tokio::time::Instant::now() >= deadline {
                    self.teardown_failed.store(true, Ordering::Release);
                    return Err(ProviderError::Protocol(
                        "native descendant remained alive after SIGKILL".into(),
                    ));
                }
                tokio::time::sleep(Duration::from_millis(20)).await;
            }
        }
        Ok(())
    }
}
