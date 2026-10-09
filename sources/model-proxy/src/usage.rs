//! Observe returned usage without changing the response forwarded to the client.
use serde_json::{Value, json};

const MAX_FRAME: usize = 1024 * 1024;

pub struct Capture {
    streaming: bool,
    line: Vec<u8>,
    data: Vec<u8>,
    skipped: bool,
    oversized_line: bool,
    truncated: bool,
    latest: Option<Value>,
}

impl Capture {
    pub fn new(streaming: bool) -> Self {
        Self { streaming, line: Vec::new(), data: Vec::new(), skipped: false, oversized_line: false,
            truncated: false, latest: None }
    }

    fn record(&mut self) {
        if !self.skipped {
            if let Ok(value) = serde_json::from_slice::<Value>(&self.data) {
                if value.get("usage").is_some_and(Value::is_object) {
                    self.latest = Some(json!({"response_id": value.get("id"),
                                             "usage": value["usage"]}));
                }
            }
        }
        self.data.clear();
        self.skipped = false;
    }

    pub fn push(&mut self, bytes: &[u8]) {
        if !self.streaming {
            if self.data.len() + bytes.len() <= MAX_FRAME && !self.skipped {
                self.data.extend_from_slice(bytes);
            } else {
                self.data.clear();
                self.skipped = true;
                self.truncated = true;
            }
            return;
        }
        for piece in bytes.split_inclusive(|byte| *byte == b'\n') {
            if self.line.len() + piece.len() <= MAX_FRAME && !self.oversized_line {
                self.line.extend_from_slice(piece);
            } else {
                self.line.clear();
                self.skipped = true;
                self.oversized_line = true;
                self.truncated = true;
            }
            if !piece.ends_with(b"\n") { continue; }
            if self.oversized_line {
                self.line.clear();
                self.oversized_line = false;
                continue;
            }
            let line = std::mem::take(&mut self.line);
            let line = line.strip_suffix(b"\n").unwrap_or(&line);
            let line = line.strip_suffix(b"\r").unwrap_or(line);
            if line.is_empty() {
                self.record();
            } else if let Some(data) = line.strip_prefix(b"data:") {
                if self.data.len() + data.len() + 1 <= MAX_FRAME && !self.skipped {
                    self.data.extend_from_slice(data.strip_prefix(b" ").unwrap_or(data));
                    self.data.push(b'\n');
                } else {
                    self.data.clear();
                    self.skipped = true;
                    self.truncated = true;
                }
            }
        }
    }

    pub fn finish(mut self, complete: bool) -> Value {
        self.record();
        json!({"status": if self.latest.is_some() {"recorded"} else {"not_returned"},
               "response_complete": complete, "capture_truncated": self.truncated,
               "returned": self.latest})
    }
}
