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
                                 cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        (TARGET/'processes.json').write_text(json.dumps({'controller_pid': os.getpid(), 'budget_guard_pid': guard.pid})+'\n')
        # The budget guard must survive a controller/network failure while the remote run continues.
        with Controller(TARGET) as controller:
            if controller.state["pending"]:
                controller.recover()
            controller.snapshot()
            for task, item in controller.state["tasks"].items():
                if item["phase"] not in {"terminal", "collected"}:
                    controller.create(task)
                    controller.start(task)
            controller.run_all(interval=480)


if __name__ == '__main__':
    main()
