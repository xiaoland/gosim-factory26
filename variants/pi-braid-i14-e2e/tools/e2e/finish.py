"""Collect the browser's non-glibc libraries for the portable addon."""
from pathlib import Path
import re
import shutil
import subprocess

root = Path('/e2e')
chrome = Path(subprocess.check_output(
    ['node', '-e', "process.stdout.write(require('playwright').chromium.executablePath())"],
    cwd=root, text=True))
nss = [Path(line) for line in subprocess.check_output(['dpkg-query', '-L', 'libnss3'], text=True).splitlines()
       if '.so' in Path(line).name and Path(line).is_file()]
platform = re.compile(r'^(?:libc|libm|libpthread|librt|libdl|libresolv)\.so(?:\.|$)|^ld-linux')
sources = {file.name: file.resolve() for file in nss}
headless = [*root.glob('browsers/chromium_headless_shell-*/*/chrome-headless-shell'),
            *root.glob('browsers/chromium_headless_shell-*/*/headless_shell')]
if not headless:
    raise FileNotFoundError('The default headless browser must be packaged')
for binary in (chrome, *headless, *nss):
    output = subprocess.check_output(['ldd', str(binary)], text=True)
    if 'not found' in output:
        raise RuntimeError(output)
    for line in output.splitlines():
        paths = [Path(field) for field in line.split() if field.startswith('/')]
        if paths:
            sources.setdefault(paths[0].name, paths[0].resolve())
(root/'lib').mkdir()
for name, source in sources.items():
    if not platform.match(name):
        shutil.copy2(source, root/'lib'/name)
