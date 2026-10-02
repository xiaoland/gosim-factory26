"""Read explicit producer facts; Console registration is not an experiment state machine."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def facts(entry):
    binding = (entry.get("docker") or {}).get("exp")
    if binding:
        root = Path(binding["experiment"])
        attempt_root = root / "attempts" / binding["attempt_id"]
        location = attempt_root / "observation.json"
        result = {"record": str(location)}
        try:
            attempt = json.loads((attempt_root / "attempt.json").read_text())
            manifest = json.loads((root / "experiment.json").read_text())
            content = location.read_bytes()
            if len(content) > 1024 * 1024:
                raise ValueError("attempt observation 超过1MiB")
            observed = json.loads(content)
            if (attempt.get("kind") != "factory26.exp.attempt" or observed.get("kind") != "factory26.exp.execution"
                    or attempt.get("attempt_id") != binding["attempt_id"]
                    or attempt.get("experiment_id") != manifest.get("experiment_id")
                    or any(observed.get(key) != attempt.get(key) for key in ("attempt_id", "experiment_id", "job_id", "dispatch_request_id"))):
                raise ValueError("生产者 attempt/experiment/observation 身份不一致")
            result.update(sha256=hashlib.sha256(content).hexdigest(), experiment_name=attempt["experiment_id"],
                          variant=(attempt["job"].get("target") or {}).get("variant"), status=observed["execution"],
                          updated_at=datetime.fromtimestamp(observed.get("live_observed_at", observed["observed_at"]), timezone.utc).isoformat())
        except (OSError, ValueError, KeyError, TypeError) as error:
            result["error"] = f"{type(error).__name__}: {error}"
        return result
    # run.json is the saved producer receipt inside an archive, not a directory-name inference.
    location = entry.get("run_record")
    if not location and entry.get("mode") == "archive":
        location = str(Path(entry["archive"]) / "run.json")
    result = {"record": location}
    if not location:
        return result
    try:
        path = Path(location)
        if not path.is_absolute():
            raise ValueError("run_record 须为生产者记录的绝对路径")
        if not entry.get("run_record") and not path.resolve().is_relative_to(Path(entry["archive"]).resolve()):
            raise ValueError("归档run.json路径越出已登记归档；未读取")
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("run_record 超过1MiB；未读取")
        content = path.read_bytes()
        result["sha256"] = hashlib.sha256(content).hexdigest()
        value = json.loads(content)
        if not isinstance(value, dict):
            raise ValueError("生产者记录须为JSON对象")
        for field in ("variant", "experiment_name", "status", "updated_at"):
            if isinstance(value.get(field), str) and value[field]:
                result[field] = value[field]
    except (OSError, ValueError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    return result
