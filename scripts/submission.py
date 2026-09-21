"""参赛入口与包内运行环境；评测由平台执行，凭据由平台注入。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
from urllib.parse import urlsplit

import factory

RESERVED = {'.arc', '.git', 'requirements', '.factory26'}


def verify_package(root):
    root = root.resolve()
    manifest = json.loads((root/'package-manifest.json').read_text())
    if (manifest.get('schema_version'), manifest.get('platform'), manifest.get('python')) != (1, 'linux-x86_64', '3.12'):
        raise ValueError('不支持的参赛制品格式')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('参赛包需要 Linux x86_64、CPython 3.12')
    files = manifest['files']
    if not files or 'package-manifest.json' in files:
        raise ValueError('参赛载荷清单无效')
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('参赛载荷不得包含符号链接')
    actual = {str(p.relative_to(root)) for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p != root/'package-manifest.json'}
    if actual != set(files):
        raise ValueError('参赛包包含缺失或未登记载荷')
    for name, record in files.items():
        path = root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('参赛载荷路径越界')
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'参赛载荷哈希不匹配：{name}')
        # Python ZIP extraction does not preserve executable permission bits.
        if record['executable']:
            path.chmod(path.stat().st_mode | 0o111)
    return manifest


def platform_config(root, manifest):
    config = factory.load_config()
    config.update(backend=manifest['backend'], runtime='submission', deployment='arcbench',
                  task='platform', benchmark_revision=None)
    visual = bool(os.environ.get('VISUAL_API_KEY') or os.environ.get('VISUAL_BASE_URL'))
    names = ('VISUAL_API_KEY', 'VISUAL_BASE_URL', 'VISUAL_MODEL') if visual else ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'MODEL')
    if any(not os.environ.get(name, '').strip() for name in names):
        raise ValueError('平台模型配置不完整：需要 ' + ', '.join(names))
    url = urlsplit(os.environ[names[1]])
    if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('平台模型地址必须是无内嵌凭据的 HTTP(S) URL')
    config.update(base_url=os.environ[names[1]], model=os.environ[names[2]],
                  key_environment=names[0], image_input=visual)
    return config


def base_environment():
    env = {name: os.environ[name] for name in ('LANG', 'LC_ALL', 'SSL_CERT_FILE', 'SSL_CERT_DIR') if name in os.environ}
    env.update(PATH=str(factory.ROOT/'runtime/bin') + ':' + str(Path(sys.executable).parent) + ':/usr/local/bin:/usr/bin:/bin',
               PYTHONPATH=str(factory.ROOT/'runtime/python'), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    return env


def adapter_environment(config, output):
    home = output/'adapter-home'
    home.mkdir()
    env = base_environment()
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home/'.config'),
               FACTORY26_API_KEY=model_key(config), LITELLM_LOCAL_MODEL_COST_MAP='True')
    return env


def environment(work, config):
    root = factory.ROOT
    home = work/'home'
    native = home/('.pi/agent' if config['backend'] == 'pi' else '.codex')
    native.mkdir(parents=True)
    (work/'tmp').mkdir()
    shutil.copy2(root/'harness/AGENTS.md', native/'AGENTS.md')
    env = base_environment()
    env.update(HOME=str(home), TMPDIR=str(work/'tmp'), XDG_CONFIG_HOME=str(home/'.config'),
               PI_CODING_AGENT_DIR=str(native), CODEX_HOME=str(native), PI_TELEMETRY='0', PI_OFFLINE='1',
               FACTORY26_API_KEY=model_key(config))
    return native, env


def model_key(config):
    value = os.environ.get(config['key_environment'], '').strip()
    if not value:
        raise ValueError('平台未注入选定模型的 API Key')
    return value


def isolation_prefix(work, inputs):
    root = factory.ROOT
    if inputs.is_relative_to(work) or root.is_relative_to(work):
        raise ValueError('只读输入和参赛制品不得位于可写工作区中')
    return [sys.executable, str(root/'scripts/linux_sandbox.py'),
            '--read', str(root), '--read', str(inputs), '--write', str(work), '--']


def preflight(prefix, work, inputs, run, env):
    marker = run/'sandbox-denied.txt'
    marker.write_text('宿主可读，Agent 不可读')
    check = '''import errno, pathlib, subprocess, sys
denied, inputs, work = map(pathlib.Path, sys.argv[1:])
def forbidden(action):
    try: action()
    except OSError as exc:
        assert exc.errno in (errno.EACCES, errno.EPERM), exc
    else: raise AssertionError('隔离未拒绝操作')
forbidden(lambda: denied.read_bytes())
source = inputs/'requirements.yaml'
source.read_bytes()
forbidden(lambda: source.open('w'))
forbidden(lambda: source.unlink())
replacement = work/'replacement'
replacement.write_text('replacement')
forbidden(lambda: replacement.replace(source))
(work/'probe').write_text('allowed')
'''
    # A grandchild must inherit the same policy, not just the initial launcher.
    command = [sys.executable, '-c', 'import subprocess,sys; subprocess.run(sys.argv[1:],check=True)',
               sys.executable, '-c', check, str(marker), str(inputs), str(work)]
    result = subprocess.run(prefix+command, cwd=work, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('参赛文件隔离预检失败：' + result.stderr)
    if marker.read_text() != '宿主可读，Agent 不可读':
        raise RuntimeError('隔离预检宿主标记已改变')
    factory.save(run/'isolation-check.json', {'mechanism':'landlock', 'evaluator_read_denied':True,
                 'requirements_readable':True, 'requirements_write_denied':True,
                 'descendants_checked':True, 'network_airgap':False})


def validate_application(app):
    for directory, script in (('frontend', 'build'), ('backend', 'start')):
        path = app/directory/'package.json'
        package = json.loads(path.read_text())
        if not isinstance(package.get('scripts', {}).get(script), str) or not package['scripts'][script].strip():
            raise ValueError(f'参赛应用缺少 {directory} 的 {script} script')
    forbidden = RESERVED.intersection(p.name for p in app.iterdir())
    if forbidden or (app/'deploy.sh').exists():
        raise ValueError('参赛应用包含平台保留路径或本地专用 deploy.sh')


def deliver(app, output):
    validate_application(app)
    entries = list(app.iterdir())
    if any((output/entry.name).exists() or (output/entry.name).is_symlink() for entry in entries):
        raise ValueError('输出目录已有同名应用文件，拒绝覆盖')
    # Validate every link before writing any platform output.
    for path in app.rglob('*'):
        if path.is_symlink() and not path.resolve().is_relative_to(app.resolve()):
            raise ValueError('应用链接指向冻结目录之外')
    for entry in entries:
        target = output/entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.git'))
        else:
            shutil.copy2(entry, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('requirements_dir', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--type', choices=['web'], default='web', help='兼容既有平台 Web 入口')
    args = parser.parse_args()
    root = factory.ROOT.resolve()
    manifest = verify_package(root)
    requirements = args.requirements_dir.resolve(strict=True)
    output = args.output_dir.resolve()
    if not (requirements/'requirements.yaml').is_file():
        raise ValueError('需求目录缺少 requirements.yaml')
    if any(p.is_symlink() for p in requirements.rglob('*')):
        raise ValueError('需求包不得包含符号链接')
    if (output == requirements or output.is_relative_to(requirements)
            or (requirements.is_relative_to(output) and requirements != output/'requirements')
            or output.is_relative_to(root) or root.is_relative_to(output)):
        raise ValueError('输出、需求及参赛包目录必须互相独立')
    config = platform_config(root, manifest)
    output.mkdir(parents=True, exist_ok=True)
    evidence = output/'.factory26'
    if evidence.is_symlink():
        raise ValueError('证据目录不能是符号链接')
    run = evidence/factory.evaluation_id()
    run.mkdir(parents=True)
    factory.save(run/'package-manifest.json', manifest)
    def interrupted(signum, frame):
        raise KeyboardInterrupt('平台终止信号')
    signal.signal(signal.SIGTERM, interrupted)
    factory.generate(config, run=run, requirements=requirements)
    try:
        deliver(run/'application', output)
    except BaseException as exc:
        factory.save(run/'delivery.json', {'status':'failed', 'error':str(exc) or type(exc).__name__})
        raise
    factory.save(run/'delivery.json', {'status':'delivered', 'application_sha256':factory.digest(factory.hashes(run/'application'))})
    print('参赛应用已交付；生成证据位于 ' + str(run), flush=True)
