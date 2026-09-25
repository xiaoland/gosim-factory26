"""Read the saved state of any lab run without interpreting its runner result."""

import json
from pathlib import Path


def read_status(run):
    run = Path(run).resolve()
    state = json.loads((run / "run.json").read_text())
    if not isinstance(state, dict) or state.get("schema_version") != 1:
        raise ValueError(f"invalid lab run record: {run / 'run.json'}")
    return {**state, "path": str(run)}
