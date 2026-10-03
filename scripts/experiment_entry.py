"""Facility entry dispatcher. Variant entries consume an already ready context."""
import json
import os
from pathlib import Path
import sys
sys.dont_write_bytecode=True


def main(root=None):
    if '--source' in sys.argv:
        import argparse
        parser=argparse.ArgumentParser(description='Run an explicit source Harness with facility-owned assembly and services')
        parser.add_argument('--source',type=Path,required=True)
        parser.add_argument('--runtime',type=Path,required=True)
        parser.add_argument('--skills',type=Path,required=True)
        parser.add_argument('--e2e-runtime',type=Path)
        args,remaining=parser.parse_known_args()
        if '--output-dir' not in remaining: raise ValueError('source execution requires --output-dir')
        output=Path(remaining[remaining.index('--output-dir')+1])
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        from execution_bootstrap import launch_source
        return launch_source(args.source,args.runtime,args.skills,remaining,output=output,e2e_runtime=args.e2e_runtime)
    root=Path(root or sys.argv[0]).resolve()
    if root.is_file(): root=root.parent
    context_path=os.environ.get('FACTORY26_EXECUTION_CONTEXT')
    if context_path:
        value=json.loads(Path(context_path).read_text())
        support=next(Path(row['local_root']) for row in value['assembly']['definitions'] if row['role']=='support')
        sys.path.insert(0,str(support))
        if '--execute-prepared' in sys.argv:
            from recover_completed import main as execute
        else:
            from run import main as execute
        return execute()
    layout=json.loads((root/'delivery-layout.json').read_text())
    namespace=Path('/factory26-namespace.json')
    deployment=json.loads(namespace.read_text()) if namespace.is_file() else {}
    if layout['mode']=='sdk-components':
        support=next(Path(row['local_root']) for row in deployment['definition_bindings'] if row['role']=='support')
    elif layout['mode']=='hosted-self-contained':
        support=root/'support'
    else:
        raise ValueError('unsupported delivery entry mode')
    sys.path.insert(0,str(support));sys.path.insert(0,str(support/'otlp-deps'))
    from execution_bootstrap import launch_delivery
    if '--output-dir' not in sys.argv:
        raise ValueError('delivery entry needs explicit --output-dir')
    output=Path(sys.argv[sys.argv.index('--output-dir')+1])
    return launch_delivery(root,sys.argv[1:],output=output,namespace=deployment.get('namespace'),
        public_environment=deployment.get('environment'),cap_bytes=deployment.get('telemetry_bytes',64*1024*1024),
        state_binding=deployment.get('state_binding'),capture_source=deployment.get('capture_source'),
        definition_bindings=deployment.get('definition_bindings'),input_bindings=deployment.get('input_bindings'))


if __name__=='__main__':
    raise SystemExit(main())
