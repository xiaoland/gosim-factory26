"""File, process and delivery operations; no Harness selection or orchestration."""
import hashlib,json,os,platform,shutil,signal,subprocess,time,uuid
from pathlib import Path

RESERVED={".arc", ".git", "requirements", ".factory26"}

def capture(*args):
    return subprocess.check_output(args,text=True).strip()

def save(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

def phase(path, metadata, name, log=None, **fields):
    now = time.time()
    metadata.update(phase=name, phase_started_at=now, updated_at=now, phase_log=log, **fields)
    save(path, metadata)

def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()
            and not {"node_modules", ".git", "__pycache__"}.intersection(p.relative_to(folder).parts)}

def copy_application(source, output):
    root=source.resolve()
    omitted={'node_modules','.git','__pycache__','.braid'}
    def ignore(folder, names):
        for name in set(names)-omitted:
            path=Path(folder)/name
            if path.is_symlink() and not path.resolve().is_relative_to(root):
                raise RuntimeError(f'应用链接指向工作区外: {path.relative_to(source)}')
        return omitted.intersection(names)
    shutil.copytree(source,output,ignore=ignore)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def signal_group(proc, sig):
    try:
        os.killpg(proc.pid,sig)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS can retain only inaccessible zombie group members after exit.
        states=capture('ps','-ax','-o','pgid=,stat=').splitlines()
        if any(line.split()[0]==str(proc.pid) and not line.split()[1].startswith('Z')
               for line in states if len(line.split())==2):
            raise

def stop(proc):
    signal_group(proc,signal.SIGTERM)
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: pass
    signal_group(proc,signal.SIGKILL)
    proc.wait()

def workspace_processes(work):
    """Include app-server tool jobs that start their own process sessions."""
    found=[]
    if platform.system()=='Linux':
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit(): continue
            try:
                cwd=(entry/'cwd').resolve(strict=True)
                if cwd.is_relative_to(work): found.append(int(entry.name))
            except (OSError,RuntimeError): pass
    else:
        result=subprocess.run(['lsof','-a','-u',str(os.getuid()),'-d','cwd','-F','pn'],capture_output=True,text=True)
        if result.returncode not in (0,1): raise RuntimeError('cannot inspect workspace processes')
        pid=None
        for line in result.stdout.splitlines():
            if line.startswith('p'): pid=int(line[1:])
            elif line.startswith('n') and pid and Path(line[1:]).is_relative_to(work): found.append(pid)
    return [pid for pid in found if pid!=os.getpid()]

def cleanup_workspace(work):
    pids=workspace_processes(work)
    for pid in pids:
        try: os.kill(pid,signal.SIGTERM)
        except ProcessLookupError: pass
    if pids: time.sleep(.2)
    for pid in workspace_processes(work):
        try: os.kill(pid,signal.SIGKILL)
        except ProcessLookupError: pass
    remaining=workspace_processes(work)
    if remaining: raise RuntimeError(f'workspace processes remain after cleanup: {remaining}')
    return pids

def logged(command, cwd, env, log, cleanup_errors=None):
    with log.open("w") as output:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=output,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return proc.wait()
        finally:
            try: stop(proc)
            except PermissionError as exc:
                # Generation has an outer, verified workspace cleanup before freezing.
                if cleanup_errors is None or proc.returncode is None: raise
                cleanup_errors.append({'pid':proc.pid,'exit_code':proc.returncode,'error':str(exc)})

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


import sys

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
