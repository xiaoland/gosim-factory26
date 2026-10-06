"""Direct I14 entry for the ARC runner."""
import json
from pathlib import Path
import sys
from harness_services import services
from run import main
if __name__=='__main__':
    package = Path(__file__).resolve().parent
    for relative in json.loads((package/'runtime-executables.json').read_text()):
        path = package/relative
        if not path.stat().st_mode & 0o111:
            path.chmod(path.stat().st_mode | 0o111)
    output = Path(sys.argv[sys.argv.index('--output-dir') + 1]).resolve()
    with services(package, output):
        main()
