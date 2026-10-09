"""Official execution returns zero so a failed generation can still be evaluated.

The native result and failure evidence remain authoritative for generation status.
Host build commands and the direct Harness CLI keep their strict exit behavior.
"""
import json
import os
from pathlib import Path
import runpy
import sys
import traceback
import uuid

root = Path(__file__).resolve().parent
failure = None
os.environ.pop('FACTORY26_ENTRY_EVIDENCE', None)
os.environ.pop('FACTORY26_NATIVE_RESULT', None)
try:
    os.environ['FACTORY26_ENTRY_PHASE'] = 'loading'
    runpy.run_path(str(root / 'harness-entry.py'), run_name='__main__')
except BaseException as error:
    # SystemExit includes argument parsing and KeyboardInterrupt includes the
    # execution owner's orderly TERM path; SIGKILL cannot run Python handlers.
    if not isinstance(error, SystemExit) or error.code not in (None, 0):
        failure = {'phase': os.environ.get('FACTORY26_ENTRY_PHASE', 'loading'),
                   'error_type': type(error).__name__, 'error': str(error),
                   'traceback': traceback.format_exc(),
                   'inner_exit_code': error.code if isinstance(error, SystemExit) else None}
        sys.stderr.write(failure['traceback'])

outcome = {'schema_version': 1, 'entry_exit_code': 0,
           'execution_succeeded': failure is None, 'generation_succeeded': False if failure else None, 'failure': failure}
try:
    evidence = os.environ.get('FACTORY26_ENTRY_EVIDENCE')
    if evidence:
        directory = Path(evidence)
        native = directory / 'result.json'
        if native.is_file():
            outcome['native_result'] = json.loads(native.read_text())
        elif os.environ.get('FACTORY26_NATIVE_RESULT'):
            outcome['native_result'] = json.loads(os.environ['FACTORY26_NATIVE_RESULT'])
        if 'native_result' in outcome:
            result = outcome['native_result']
            outcome['generation_succeeded'] = result.get('exit_code') == 0 and result.get('terminal') == 'stop'
        errors = directory / 'execution-errors.jsonl'
        if errors.is_file():
            outcome['stage_errors'] = [json.loads(line) for line in errors.read_text().splitlines() if line]
            if outcome['stage_errors']:
                outcome['execution_succeeded'] = False
    else:
        # Early parsing/setup errors may happen before a native run exists.
        output = next((sys.argv[i + 1] for i, value in enumerate(sys.argv[:-1]) if value == '--output-dir'), None)
        directory = (Path(output).resolve() if output else root) / '.factory26/pi-minimal-vv/entry-failures' / uuid.uuid4().hex
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'entry-outcome.json').write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + '\n')
except BaseException:
    # Evidence failure must also preserve its concrete traceback, without
    # defeating the explicitly selected official exit contract.
    traceback.print_exc()
finally:
    try:
        print(json.dumps({'factory26_entry_outcome': outcome}, ensure_ascii=False), flush=True)
    except BaseException:
        try:
            traceback.print_exc()
        except BaseException:
            pass
    finally:
        sys.exit(0)
