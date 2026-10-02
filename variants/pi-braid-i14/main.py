"""官方及源码开发共用的 Agent 入口。"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
support=root/'support' if (root/'support').is_dir() else root.parents[1]/'scripts'
sys.path.insert(0,str(support))
if (root/'package-manifest.json').is_file():
    from agent_support import verify_package
    verify_package(root)
if '--execute-prepared' in sys.argv:
    # Delivered support is frozen with the material; development uses the same producer.
    if not (root/'recover_completed.py').is_file():
        sys.path.insert(0,str(root.parents[1]/'submission'))
    from recover_completed import main
else:
    from run import main
if __name__=='__main__':
    main()
