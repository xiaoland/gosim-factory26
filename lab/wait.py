"""Wait quietly for existing lab runs; emit terminal records only."""
import argparse
import json
import os
from pathlib import Path
import time

from .control import owner_state, wait_for_change
from .status import read_status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', type=Path, nargs='+')
    parser.add_argument('--controller-pid', type=int)
    args = parser.parse_args()
    pending = list(dict.fromkeys(path.resolve(strict=True) for path in args.runs))
    cursors = {}
    while pending:
        experiment = None
        for run in pending[:]:
            record = read_status(run)
            if record['phase'] in {'completed', 'failed', 'interrupted', 'finished', 'cancelled', 'lost'}:
                event = {key: record.get(key) for key in
                         ('run_id', 'phase', 'result_path', 'runner_exit_code', 'error')}
                event['record'] = str(run/'run.json')
                print(json.dumps(event, ensure_ascii=False), flush=True)
                pending.remove(run)
            elif record.get('schema_version') == 2:
                candidate = run.parent.parent
                if not (candidate / 'manifest.json').is_file():
                    candidate = run.parent / '.experiments' / record['experiment_id']
                experiment = candidate
        if not pending:
            return
        if experiment is not None:
            owner_path = experiment / 'active.json'
            owner = json.loads(owner_path.read_text()) if owner_path.is_file() else None
            if owner_state(owner) != 'alive' or owner.get('phase') != 'running':
                raise SystemExit(f'Controller ownership unconfirmed for {experiment}; use lab reconcile')
            key = owner['controller_id']
            if key not in cursors:
                log = experiment / 'controllers' / key / 'notifications.jsonl'
                rows = log.read_text().splitlines() if log.is_file() else []
                cursors[key] = json.loads(rows[-1])['seq'] if rows else 0
            cursors[key] = wait_for_change(experiment, cursors[key])['events']
            continue
        if args.controller_pid is not None:
            try:
                os.kill(args.controller_pid, 0)
            except ProcessLookupError:
                raise SystemExit(f'Controller {args.controller_pid} exited while runs remain nonterminal: {pending}')
            except PermissionError:
                pass  # The process exists but belongs to another user.
        time.sleep(180)


if __name__ == '__main__':
    main()
