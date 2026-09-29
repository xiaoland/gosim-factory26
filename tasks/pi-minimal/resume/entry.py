"""Local continuation of the stopped Pi application and native session."""
import argparse
import json
from pathlib import Path
import shutil
import stat
from zipfile import ZipFile

root = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('requirements')
p.add_argument('--output-dir', type=Path, required=True)
p.add_argument('--type', default='web')
a = p.parse_args()
output = a.output_dir.resolve()
if (output/'.arc/pi-minimal/session.jsonl').exists():
    raise RuntimeError('Continuation destination already contains a Pi session')
with ZipFile(root/'retained-workspace.zip') as archive:
    for entry in archive.infolist():
        relative = Path(entry.filename)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'Invalid retained path: {relative}')
        target = output/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(entry) as incoming, target.open('wb') as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        mode = stat.S_IMODE(entry.external_attr >> 16)
        if mode:
            target.chmod(mode)
(output/'.arc/pi-minimal/resume-source.json').write_text((root/'resume-source.json').read_text())
print('Pi continuation: retained application and session restored; applying updated capabilities', flush=True)
import pi_main
pi_main.main()
