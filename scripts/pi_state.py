"""Pi state-file ownership repair for native adapters, not run orchestration."""
import os
from pathlib import Path
import stat


def repair_state_files(output, roots):
    """Return Pi's root-created private files to the mounted output owner."""
    if os.geteuid() != 0:
        return []
    try:
        owner = Path(output).stat()
    except OSError as error:
        return [{'path': str(output), 'error': str(error)}]
    errors = []
    for root in roots:
        for name in ('auth.json', 'models-store.json'):
            for path in Path(root).rglob(name):
                try:
                    info = path.lstat()
                    if stat.S_ISREG(info.st_mode) and not path.is_symlink() and (
                            info.st_uid, info.st_gid) != (owner.st_uid, owner.st_gid):
                        os.chown(path, owner.st_uid, owner.st_gid, follow_symlinks=False)
                except OSError as error:
                    errors.append({'path': str(path), 'error': str(error)})
    return errors
