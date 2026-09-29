"""Run the approved two-task journal with an independent ten-minute budget guard."""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lab.arc_bench.competition import Controller
from lab.arc_bench.playground import Client
from budget_guard import TARGET, check_once


def main():
    result = check_once(TARGET, Client())
    if result['status'] != 'clear':
        print(json.dumps(result), flush=True)
        raise SystemExit(2)
    with (TARGET/'budget-monitor.log').open('a') as log:
        guard = subprocess.Popen([sys.executable, '-u', str(Path(__file__).with_name('budget_guard.py')), str(TARGET)],
                                 cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        (TARGET/'processes.json').write_text(json.dumps({'controller_pid': os.getpid(), 'budget_guard_pid': guard.pid})+'\n')
        try:
            with Controller(TARGET) as controller:
                controller.run_all(interval=480)
        finally:
            guard.terminate()
            guard.wait(timeout=20)


if __name__ == '__main__':
    main()
