"""Variant entry: execution services and placements belong to the facility."""
import json
import os
from pathlib import Path
import sys
sys.dont_write_bytecode=True
context_path=os.environ.get('FACTORY26_EXECUTION_CONTEXT')
if not context_path:
    raise ValueError('Harness entry requires a ready execution context; use the facility entry')
context=json.loads(Path(context_path).read_text())
support=next(Path(row['local_root']) for row in context['assembly']['definitions'] if row['role']=='support')
sys.path.insert(0,str(support));sys.path.insert(0,str(support/'otlp-deps'))
from experiment_entry import main
if __name__=='__main__':
    main(Path(__file__).parent)
