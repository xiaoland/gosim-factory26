"""ZIP 根入口：只生成并交付应用，评测由平台执行。"""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent/'scripts'))
from submission import main

if __name__ == '__main__':
    main()
