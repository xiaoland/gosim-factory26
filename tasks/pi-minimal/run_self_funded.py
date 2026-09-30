"""Run both approved tasks with the credentials bundled in the frozen package."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'scripts'))
from hackathon_gateway import read_assignments
from lab.arc_bench.competition import Controller


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('journal', type=Path)
    journal = parser.parse_args().journal.resolve()
    inputs = json.loads((journal/'inputs.json').read_text())
    if inputs['credential_mode'] != 'self_funded':
        raise ValueError('This experiment must not use competition credit')
    (journal/'controller-process.json').write_text(json.dumps({'pid': os.getpid()})+'\n')
    credentials = read_assignments(ROOT/'.secrets/models.env')
    with Controller(journal, secret=credentials['GLM_API_KEY']) as controller:
        if controller.state['pending']:
            controller.recover()
        controller.snapshot()
        print(json.dumps({'submission_id': controller.state['submission_id']}), flush=True)
        for task, item in controller.state['tasks'].items():
            if item['phase'] not in {'terminal', 'collected'}:
                controller.create(task)
                controller.start(task)
                print(json.dumps({'task': task, 'run_id': item['run_id']}), flush=True)
        controller.run_all(interval=480)


if __name__ == '__main__':
    main()
