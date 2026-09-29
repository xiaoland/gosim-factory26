#!/usr/bin/env bash
set -euo pipefail

agent_zip=${1:?usage: matrix.sh AGENT_ZIP --inputs-root DIR --runner DIR --image IMAGE --output FILE [arc_matrix options]}
shift
cd "$(dirname "$0")/../.."
exec python3 -m lab.arc_bench.arc_matrix \
  --variant "pi-braid=$agent_zip" \
  --case arc-bench-lite/keep \
  --case arc-bench-lite/bookstack \
  --separate-evaluation \
  "$@"
