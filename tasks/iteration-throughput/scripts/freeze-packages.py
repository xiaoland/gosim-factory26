"""复用本轮已验收的 Pi runtime，装配四个配置不同的最终 ZIP。"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
import competition
import package_agent
import profiles
import sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('sha256')
    parser.add_argument('output', type=Path)
    parser.add_argument('--build-inputs', required=True, type=Path,
                        help='资格构建时记录的 {submission/Dockerfile: sha256, submission/build.py: sha256}')
    args = parser.parse_args()
    if competition.digest(args.candidate) != args.sha256:
        raise ValueError('资格候选 ZIP 已改变')
    build_inputs = json.loads(args.build_inputs.read_text())
    if set(build_inputs) != {'submission/Dockerfile', 'submission/build.py'}:
        raise ValueError('必须记录两个实际构建输入')
    for name, expected in build_inputs.items():
        if competition.digest(ROOT/name) != expected:
            raise ValueError('构建输入已改变，不能复用 runtime: '+name)
    original = competition.package_identity(args.candidate)
    if original['backend'] != 'pi':
        raise ValueError('本次装配只支持已验收的 Pi runtime')
    records = {name: sources.snapshot(name) for name in ('svc', 'braid')}
    for name, record in records.items():
        if record['files'] != original['sources'][name]['files']:
            raise ValueError(name+' 源文件变化，必须重建')
    for name, record in original['files'].items():
        source = ROOT/('submission/main.py' if name == 'main.py' else name)
        if name == 'main.py' or name.startswith(('scripts/', 'harness/')):
            if competition.digest(source) != record['sha256']:
                raise ValueError('consumer 输入变化，必须重新资格: '+name)
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix='qualified-runtime-', dir=args.output) as temporary:
        bundle = Path(temporary)
        with ZipFile(args.candidate) as archive:
            archive.extractall(bundle)
        for name, record in original['files'].items():
            (bundle/name).chmod(0o755 if record['executable'] else 0o644)
        for variant in ('pi-team-deepseek', 'pi-team-glm', 'pi-team-mixed', 'pi-team-vv'):
            shutil.rmtree(bundle/'variants')
            shutil.copytree(ROOT/'variants'/variant, bundle/'variants'/variant)
            config = profiles.configuration(variant)
            config['deployment'] = 'arcbench'
            frozen = bundle/'variants/factory/config.json'
            frozen.parent.mkdir()
            frozen.write_text(json.dumps(config, indent=2)+'\n')
            destination = args.output/(variant+'.zip')
            package_agent.write_zip(bundle, destination, 'pi', records,
                                    package_agent.capability_manifest(config['effective'], records))
            competition.package_identity(destination)
            rows.append({'variant': variant, 'path': str(destination.resolve()),
                         'sha256': competition.digest(destination)})
            print(json.dumps(rows[-1]), flush=True)
    (args.output/'qualification-source.json').write_text(json.dumps({
        'candidate': str(args.candidate.resolve()), 'candidate_sha256': args.sha256,
        'build_inputs': build_inputs, 'packages': rows}, indent=2)+'\n')


if __name__ == '__main__':
    main()
