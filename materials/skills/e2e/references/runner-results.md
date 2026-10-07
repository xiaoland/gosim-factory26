# Interpret the frozen runner's results

Read this after an e2e application check when an exit, model response, exploration result or usage report could change acceptance or consumption accounting. Identify the installed e2e version from its package metadata or addon-source receipt, then use its `e2e guide running` and CLI help; do not apply a version-specific limitation to an unrelated runner.

The current Factory addon locks e2e 0.15.1 and @e2e-dev/web 0.11.1. Its exits distinguish application failure (1), config/dependency/policy failure (2), infrastructure/provider/cleanup failure (3), internal failure (4) and interruption (130). Preserve the concrete error and HTTP response, not just the exit category. None of these is a verified pass. Startup errors can leave a previous report unchanged, so bind each report to the attempt that produced it.

For this release, inspect repaired `MODEL_OUTPUT_INVALID` responses and failed steps even when the run passes. A rejected schema response can be omitted from report usage; count all model round trips in `ai-trace.json` when recording consumption. Keep screenshots separately because image bytes are replaced by counts in that trace. An exploration can fall back from a failed planner and end at its step limit, so exit 0 does not by itself establish the original exploration goal or requirement coverage.

A new runner version requires rechecking these interpretations against its actual CLI, guide and response evidence. The application requirements and observed outcomes remain the acceptance basis across versions.
