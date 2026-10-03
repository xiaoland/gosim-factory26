"""官方及源码开发共用的 Agent 入口。"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
context_path=__import__('os').environ.get('FACTORY26_EXECUTION_CONTEXT')
if context_path:
    context=__import__('json').loads(Path(context_path).read_text())
    roles={row['role']:Path(row['local_root']) for row in context['assembly']['definitions']}
    support=roles['support']
else:
    support=root/'support' if (root/'support').is_dir() else root.parents[1]/'scripts'
sys.path.insert(0,str(support))
if (support/'otlp-deps').is_dir(): sys.path.insert(0,str(support/'otlp-deps'))
if not context_path and (root/'delivery-layout.json').is_file():
    from execution_bootstrap import launch_delivery
    if '--output-dir' not in sys.argv:
        raise ValueError('delivery entry needs explicit --output-dir')
    output=Path(sys.argv[sys.argv.index('--output-dir')+1])
    namespace_file=Path('/factory26-namespace.json')
    deployment=__import__('json').loads(namespace_file.read_text()) if namespace_file.is_file() else {}
    raise SystemExit(launch_delivery(root,sys.argv[1:],output=output,namespace=deployment.get('namespace'),
                                    public_environment=deployment.get('environment'),cap_bytes=deployment.get('telemetry_bytes',64*1024*1024),
                                    state_binding=deployment.get('state_binding'),capture_source=deployment.get('capture_source'),
                                    definition_store=deployment.get('definition_store'),definition_bindings=deployment.get('definition_bindings')))
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
