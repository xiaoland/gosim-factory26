"""Preserve execution output links without following them across the workspace boundary."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile


def output_inventory(root):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f'output must be a regular directory: {root}')
    entries = []
    for path in sorted(root.rglob('*'), key=lambda p: p.relative_to(root).as_posix()):
        row = {'path': path.relative_to(root).as_posix()}
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            row.update(type='link', target=os.readlink(path))
        elif stat.S_ISREG(mode):
            with path.open('rb') as stream:
                row.update(type='file', sha256=hashlib.file_digest(stream, 'sha256').hexdigest(),
                           executable=bool(mode & 0o111))
        elif stat.S_ISDIR(mode):
            row['type'] = 'directory'
        else:
            raise ValueError(f'non-file execution output: {row["path"]}')
        entries.append(row)
    encoded = json.dumps(entries, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return {'algorithm': 'workspace-output-sha256-v1', 'sha256': hashlib.sha256(encoded).hexdigest(),
            'kind': 'directory', 'entries': entries}


def extract_output(archive, destination):
    """Extract data before links, so no archive member can write through a preserved link."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        named = {}
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or '\\' in member.name:
                raise ValueError(f'unsafe archive path: {member.name}')
            name = str(path)
            if name == '.':
                if not member.isdir():
                    raise ValueError('archive root must be a directory')
                continue
            if name in named:
                raise ValueError(f'duplicate archive path: {name}')
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise ValueError(f'unsupported archive member: {name}')
            named[name] = member
        for name, member in named.items():
            for parent in PurePosixPath(name).parents:
                ancestor = named.get(str(parent))
                if ancestor is not None and not ancestor.isdir():
                    raise ValueError(f'archive writes through non-directory: {name}')
            if member.islnk():
                target = named.get(str(PurePosixPath(member.linkname)))
                if target is None or not target.isfile():
                    raise ValueError(f'hard link target is not archived regular data: {name}')
        stream.extractall(destination, members=[m for m in members if not m.issym()], filter='data')
        for name, member in named.items():
            if member.issym():
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(member.linkname)
