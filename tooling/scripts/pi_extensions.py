"""Select maintained Pi extension sources and preserve their delivery paths."""
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'materials/pi-extensions'
_COMMON = ('exa.ts', 'factory-pi-timing.ts')
_VARIANT = {
    'pi-minimal-vv': ('capability-evidence.ts', 'owned-e2e.ts'),
    'pi-braid-i15-reviewer-cleaner-e2e': ('factory-cleaner.ts', 'factory-cleaner.md',
                                      'factory-subagent-observer.ts'),
}


def extension_sources(variant):
    """Historical variants keep their frozen local extension ownership."""
    if variant not in _VARIANT:
        return {}
    local = ROOT/'variants'/variant/'extensions'
    if local.exists() and any(path.is_file() for path in local.rglob('*')):
        raise ValueError('Maintained Pi extensions belong in materials/pi-extensions, not '+str(local))
    return {**{name: SOURCE/name for name in _COMMON},
            **{name: SOURCE/variant/name for name in _VARIANT[variant]}}


def extension_identity(variant):
    """Bind source selection and actual bytes to a producer/cache identity."""
    return {name: {'source': str(path.relative_to(ROOT)),
                   'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for name, path in extension_sources(variant).items()}


def copy_extensions(variant, destination):
    """Flatten selected files into the existing extensions/ delivery directory.

    owned-e2e.ts imports ../tools/owned-e2e.mjs at that location. Copying real
    files preserves that contract; links to the source tree would break it.
    """
    sources = extension_sources(variant)
    if not sources:
        return {}
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    before = extension_identity(variant)
    for name, source in sources.items():
        shutil.copy2(source, destination/name)
    if extension_identity(variant) != before or any(
            hashlib.sha256((destination/name).read_bytes()).hexdigest() != row['sha256']
            for name, row in before.items()):
        raise ValueError('Pi extension source changed during material production')
    return before
