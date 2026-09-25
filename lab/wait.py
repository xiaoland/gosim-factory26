"""Wait quietly for existing lab runs; emit terminal records only."""
import argparse
import json
import os
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', type=Path, nargs='+')
    parser.add_argument('--controller-pid', type=int)
    args = parser.parse_args()
    pending = list(dict.fromkeys(path.resolve(strict=True) for path in args.runs))
    while pending:
        for run in pending[:]:
            record = json.loads((run/'run.json').read_text())
            if record['phase'] in {'completed', 'failed', 'interrupted'}:
                event = {key: record.get(key) for key in
                         ('run_id', 'phase', 'result_path', 'runner_exit_code', 'error')}
                event['record'] = str(run/'run.json')
                print(json.dumps(event, ensure_ascii=False), flush=True)
                pending.remove(run)
        if not pending:
            return
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
