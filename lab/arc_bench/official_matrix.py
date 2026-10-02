"""Freeze one hosted job per explicit platform task in the new exp contract."""
import argparse
import json
from pathlib import Path

from lab.exp.core import record


def build(spec):
    """Only a new recipe is accepted; fee/provider policy is always explicit."""
    from lab.exp.core import require
    if spec.get('kind') == 'factory26.exp.hosted-matrix':
        require(spec, 'hosted-matrix')
        jobs = []
        for variant in spec['variants']:
            for competition in spec['competitions']:
                for task in competition['tasks']:
                    jobs.append({'id': variant['id'] + '--' + competition['id'] + '--' + task['id'],
                                 'purpose': variant['purpose'],
                                 'inputs': {'agent': {'source': variant['package']}}, 'outputs': [],
                                 'limits': variant['limits'],
                                 'backend': {'kind': 'hosted', 'competition_id': competition['id'],
                                             'variant': variant['id'], 'task': task['id'],
                                             'model_config': variant['model_config'],
                                             'credential_mode': variant['credential_mode'],
                                             'allow_competition_credit': variant['allow_competition_credit']}})
        spec = record('experiment', **{key: spec[key] for key in
                      ('experiment_id', 'authorization', 'max_parallel', 'controller_runtime', 'storage', 'budget')}, jobs=jobs)
    else:
        require(spec, 'experiment')
    for job in spec['jobs']:
        backend = job['backend']
        if backend['kind'] != 'hosted' or job['purpose'] not in {'generate', 'evaluate'}:
            raise ValueError('official matrix requires explicit single-task hosted jobs')
        if any(key not in backend for key in ('competition_id', 'variant', 'task', 'model_config', 'credential_mode', 'allow_competition_credit')):
            raise ValueError('hosted job lacks frozen platform/model/fee policy')
        if 'provider' not in backend['model_config']:
            raise ValueError('hosted model provider must be explicit')
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--deployment', type=Path)
    args = parser.parse_args()
    from lab.exp.controller import build as freeze, start
    recipe = build(json.loads(args.manifest.read_text()))
    frozen_recipe = args.manifest.with_name(args.manifest.stem + '.exp.json')
    frozen_recipe.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n')
    freeze(frozen_recipe, args.directory)
    root = args.directory.resolve()
    print(root)
    if not args.build_only:
        print(json.dumps(start(root, deployment=args.deployment), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
