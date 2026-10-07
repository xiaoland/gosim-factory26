"""Standalone I15 generation entry for a manual private API run."""
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent/'support'))
from run import main
if __name__=='__main__':
    main()
