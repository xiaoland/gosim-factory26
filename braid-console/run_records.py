"""Read explicit producer facts; Console registration is not an experiment state machine."""

import hashlib
import json
from pathlib import Path


def facts(entry):
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
