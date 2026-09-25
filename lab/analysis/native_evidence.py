"""Locate optional Harness process evidence beside an ARC Runner workspace."""

import json
from pathlib import Path


def discover(run, detail):
    run = Path(run)
    evidence = detail["evidence"]
    warnings = detail["warnings"]
    factory_runs, native = [], []

    def link(path):
        if path.exists():
            evidence[str(path.relative_to(run))] = str(path)
        return path

    for name in ("official-generation", "official-evaluation", "official"):
        app = run / "workspace" / name / "template"
        if not app.is_dir():
            continue
        for path in sorted((app / ".factory26").glob("*/run.json")):
            factory_runs.append(str(path.parent))
            link(path)
            try:
                data = json.loads(path.read_text())
                if name != "official-evaluation" and detail["generation"]["status"] == "unknown":
                    detail["generation"].update(status=data.get("status") or "unknown",
                                                exit_code=data.get("process_exit_code"),
                                                error=data.get("error"))
                manifest = path.parent / "native/manifest.json"
                if manifest.is_file():
                    for entry in json.loads(link(manifest).read_text()).get("sessions", []):
                        if entry.get("native"):
                            native.append(str(link(path.parent / entry["native"])))
            except (OSError, ValueError, TypeError) as exc:
                warnings.append(f"{path}: {exc}")
            for item in ("application", "braid.log", "delivery.json", "braid-state"):
                link(path.parent / item)
        for folder_name in ("raw", "hackathon"):
            folder = app / ".arc" / folder_name
            if not folder.is_dir():
                continue
            for pattern in ("*.json", "*.jsonl", "*.log", "home/.codex/sessions/**/*.jsonl"):
                for path in folder.glob(pattern):
                    link(path)
                    if path.suffix == ".jsonl" and path.name != "events.jsonl":
                        native.append(str(path))
            if name != "official-evaluation" and detail["generation"]["status"] == "unknown":
                result = folder / "entry-result.json"
                if result.is_file():
                    try:
                        value = json.loads(link(result).read_text())
                        detail["generation"].update(value, status=value.get("status") or "unknown")
                    except (OSError, ValueError, TypeError) as exc:
                        warnings.append(f"{result}: {exc}")
    return {"factory_runs": factory_runs, "native": sorted(set(native))}
