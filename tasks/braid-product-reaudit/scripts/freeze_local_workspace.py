"""Archive a stopped local Runner template, retaining Git files and symlinks."""
import argparse
import os
from pathlib import Path
import stat
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('template', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
a.output.parent.mkdir(parents=True, exist_ok=True)
count = 0
with a.output.open('xb') as stream, ZipFile(stream, 'w', compression=ZIP_DEFLATED, compresslevel=1) as archive:
    for directory, folders, files in os.walk(a.template, followlinks=False):
        for name in folders[:] + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            entry = 'template/' + path.relative_to(a.template).as_posix()
            if stat.S_ISLNK(mode):
                info = ZipInfo(entry)
                info.create_system = 3
                info.external_attr = mode << 16
                archive.writestr(info, os.readlink(path))
                if name in folders:
                    folders.remove(name)
            elif stat.S_ISREG(mode):
                archive.write(path, entry)
            elif stat.S_ISDIR(mode):
                continue
            elif stat.S_ISSOCK(mode):
                continue  # A stopped process's socket is not restorable state.
            else:
                raise ValueError(f'unsupported workspace entry: {path}')
            count += 1
print(f'{a.output}: {count} entries, {a.output.stat().st_size} bytes', flush=True)
