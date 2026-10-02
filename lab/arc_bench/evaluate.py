"""Build an independent evaluation of an explicitly frozen application artifact."""
import argparse
import json
from pathlib import Path

from lab.exp.core import record, require, read


def prepare(application, output, *, host_runtime_receipt, runner_runtime_receipt,
            storage, budget, resource_limits, requirements, tests, runner, image, endpoint, admission_volume,
            competition, task, application_receipt, source_attempt, selection=None,
            experiment_key='arc-evaluation', slots=1, authorization=None, authority_handoff=None):
    """No source-run path inference or inherited model/fee permission is performed."""
    from lab.exp.controller import build
    adapter = Path(__file__).resolve().parent
    inputs = {'application': application,
              'application_receipt': application_receipt, 'requirements': requirements,
              'tests': tests, 'runner': runner, 'noop': {'source': str(adapter / 'arc_bench_noop.py')}}
    command = [require(read(runner_runtime_receipt), 'runtime')['launcher'], '-m', 'lab.arc_bench.arc_bench_adapter', '--runner', '{runner}',
               '--application', '{application}', '--application-receipt', '{application_receipt}',
               '--noop-script', '{noop}', '--requirements', '{requirements}', '--tests', '{tests}',
               '--workspace', '{workspace}', '--competition', competition, '--task', task,
               '--image', image, '--source-run-id', source_attempt,
               '--admission-volume', admission_volume, '--shared-docker-slots', str(slots)]
    if selection:
        inputs['selection'] = selection
        command += ['--selection', '{selection}']
    spec = record('experiment', experiment_id=experiment_key, max_parallel=1, storage=storage, budget=budget, authorization=authorization,
                  controller_runtime=str(Path(host_runtime_receipt).resolve()),
                  runner_runtime=str(Path(runner_runtime_receipt).resolve()),
                  jobs=[{'id': 'evaluation', 'purpose': 'evaluate', 'inputs': inputs, 'command': command,
                         'source_attempt': source_attempt,
                         'backend': {'kind': 'local', 'capabilities_required': ['arc-sdk-host-docker'],
                                     'external_docker': {'endpoint': endpoint, 'image_id': image, 'slots': slots,
                                                         'admission_volume': admission_volume, 'authority_handoff': authority_handoff}},
                         'outputs': [{'name': 'workspace', 'type': 'terminal-archive', 'path': '.'},
                                     {'name': 'score', 'type': 'evaluation-result', 'path': 'experiment-result.json'}],
                         'limits': {'wall_seconds': budget['wall_seconds_per_attempt'],
                                    'storage_bytes': storage['workspace_bytes_per_run'],
                                    'telemetry_bytes': storage['telemetry_bytes_per_run'], **resource_limits}}])
    recipe = Path(output).with_name(Path(output).name + '.recipe.json')
    recipe.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
    build(recipe, output)
    return Path(output).resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True, help='new exp evaluation recipe with explicit artifact inputs')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args(argv)
    spec = require(json.loads(args.spec.read_text()), 'experiment')
    if any(job['purpose'] != 'evaluate' for job in spec['jobs']):
        raise ValueError('evaluation recipe may contain only evaluate jobs')
    from lab.exp.controller import build, start
    build(args.spec, args.output)
    root = args.output.resolve()
    print(root)
    if not args.build_only:
        print(json.dumps(start(root), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
