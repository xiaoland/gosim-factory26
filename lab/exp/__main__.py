"""The new experiment contract. Legacy inputs are only accessible through history."""
import argparse
import json
from pathlib import Path
import time

from . import artifacts, controller, history
from .core import atomic, public, read, record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    compiled = commands.add_parser('compile', help='将显式 intent 编译为冻结 recipe，不安装或运行')
    compiled.add_argument('intent', type=Path)
    compiled.add_argument('--directory', type=Path, required=True)
    compiled.add_argument('--environment', type=Path)
    doctor = commands.add_parser('doctor', help='只读检查声明资产和宿主，不安装或预约')
    doctor.add_argument('recipe', type=Path)
    doctor.add_argument('--deployment', type=Path)
    doctor.add_argument('--json', action='store_true')
    doctor.add_argument('--environment', type=Path)
    build = commands.add_parser('build')
    build.add_argument('recipe', type=Path)
    build.add_argument('--directory', type=Path, required=True)
    build.add_argument('--environment', type=Path)
    recover = commands.add_parser('recover', help='派生新run；同域模式在capture许可内修复状态，不启动模型')
    recover.add_argument('source', type=Path)
    recover.add_argument('--intent', type=Path, required=True)
    recover.add_argument('--environment', type=Path, required=True)
    recover.add_argument('--directory', type=Path, required=True)
    checkpoint = commands.add_parser('checkpoint', help='受管关闭全部登记writer并封存checkpoint；不接受手填closure')
    checkpoint.add_argument('experiment', type=Path)
    checkpoint.add_argument('attempt')
    checkpoint.add_argument('--directory', type=Path, required=True)
    checkpoint.add_argument('--request-id')
    checkpoint.add_argument('--source-resource', help='明确选择已验证终态SDK child的authority resource id')
    start = commands.add_parser('start')
    start.add_argument('experiment', type=Path)
    start.add_argument('--deployment', type=Path)
    continuation = commands.add_parser('continue-pre-reserve', help='严格核实无预约及执行资源后，同 attempt 接续 reserve 前 inspect 超时；保留冻结来源')
    continuation.add_argument('attempt_directory', type=Path)
    upload = commands.add_parser('continue-input-upload', help='严格核实原创建容器从未启动后，接续同 attempt 上传及启动')
    upload.add_argument('attempt_directory', type=Path)
    confirm_start = commands.add_parser('confirm-start-binding', help='仅闭合已启动且等待marker的原容器绑定，不调用start')
    confirm_start.add_argument('attempt_directory', type=Path)
    for name in ('status', 'monitor', 'wait'):
        item = commands.add_parser(name)
        item.add_argument('experiment', type=Path)
        item.add_argument('--json', action='store_true')
        if name == 'wait':
            item.add_argument('--timeout', type=float, default=60)
    control = commands.add_parser('control')
    control.add_argument('experiment', type=Path)
    control.add_argument('attempt')
    control.add_argument('command', choices=['stop', 'pause', 'resume', 'export', 'repair-ready'])
    control.add_argument('--request-id')
    control.add_argument('--service', choices=['collector', 'resource_evidence'])
    stopped = commands.add_parser('stop-evidence')
    stopped.add_argument('experiment', type=Path)
    stopped.add_argument('attempt')
    stopped.add_argument('--output', type=Path, required=True)
    imported_stop = commands.add_parser('import-source-stop', help='导入官网独立 GET 原件，旧来源或绑定实际 experiment/attempt；不授予启动许可')
    imported_stop.add_argument('--experiment', type=Path)
    imported_stop.add_argument('--attempt')
    imported_stop.add_argument('--birth', type=Path, required=True)
    imported_stop.add_argument('--status', type=Path, required=True)
    imported_stop.add_argument('--cancel-evidence', type=Path)
    imported_stop.add_argument('--authorization', required=True)
    imported_stop.add_argument('--identity-output', type=Path, required=True)
    imported_stop.add_argument('--output', type=Path, required=True)
    docker_stop = commands.add_parser('import-docker-source-stop', help='核对旧 Docker 停止与 writer 原件，保留 legacy 来源身份')
    docker_stop.add_argument('--birth', type=Path, required=True)
    docker_stop.add_argument('--status', type=Path, required=True)
    docker_stop.add_argument('--writers', type=Path, required=True)
    docker_stop.add_argument('--authorization', required=True)
    docker_stop.add_argument('--identity-output', type=Path, required=True)
    docker_stop.add_argument('--output', type=Path, required=True)
    retry = commands.add_parser('retry')
    retry.add_argument('experiment', type=Path)
    retry.add_argument('attempt')
    retry.add_argument('--authorization', required=True)
    retry.add_argument('--request-id')
    authority = commands.add_parser('authority-handoff')
    authority.add_argument('--endpoint', type=Path, required=True)
    authority.add_argument('--writer', type=Path, action='append', default=[])
    authority.add_argument('--registry', type=Path)
    authority.add_argument('--mode', choices=['retirement', 'first-use'], default='retirement')
    authority.add_argument('--scope', type=Path)
    authority.add_argument('--authorization', required=True, help='明确确认已列出该 daemon 的全部旧派发者')
    authority.add_argument('--output', type=Path, required=True)
    telemetry = commands.add_parser('telemetry')
    tactions = telemetry.add_subparsers(dest='telemetry_action', required=True)
    for name in ('snapshot', 'batches', 'export'):
        item = tactions.add_parser(name)
        item.add_argument('attempt', type=Path)
        if name != 'snapshot':
            item.add_argument('--after', type=int, default=0)
            item.add_argument('--until', type=int)
        if name == 'export':
            item.add_argument('--output', type=Path, required=True)
    ingested = tactions.add_parser('ingest')
    ingested.add_argument('transport', type=Path)
    ingested.add_argument('--output', type=Path, required=True)
    analyze = commands.add_parser('analyze')
    analyze.add_argument('experiment', type=Path)
    analyze.add_argument('--output', required=True, type=Path)
    historic = commands.add_parser('history')
    historic.add_argument('source', type=Path)
    artifact = commands.add_parser('artifact')
    actions = artifact.add_subparsers(dest='artifact_action', required=True)
    imported = actions.add_parser('import')
    imported.add_argument('source', type=Path)
    imported.add_argument('--store', type=Path, required=True)
    imported.add_argument('--type', default='evidence')
    imported.add_argument('--provenance', type=Path)
    imported.add_argument('--output', type=Path, help='保存本次发布引用，供下游消费')
    transferred = actions.add_parser('transfer')
    transferred.add_argument('reference', type=Path)
    transferred.add_argument('--source-store', type=Path, required=True)
    transferred.add_argument('--store', type=Path, required=True)
    for name in ('verify', 'export'):
        item = actions.add_parser(name)
        item.add_argument('reference', type=Path)
        item.add_argument('--store', type=Path, required=True)
        if name == 'export':
            item.add_argument('--output', type=Path, required=True)
    evidence = commands.add_parser('evidence')
    evidence.add_argument('reference', type=Path)
    evidence.add_argument('--store', type=Path, required=True)
    evidence.add_argument('--member', default='.')
    evidence.add_argument('--offset', type=int, default=0)
    evidence.add_argument('--bytes', type=int, default=4096)
    args = parser.parse_args(argv)
    if args.action == 'compile':
        from .compiler import compile_intent
        value = compile_intent(args.intent, args.directory, environment=args.environment)
    elif args.action == 'doctor':
        from . import readiness
        value = readiness.inspect(args.recipe, args.deployment, environment=args.environment)
        if not args.json:
            print(readiness.render(value))
            return 0
    elif args.action == 'build':
        value = controller.build(args.recipe, args.directory, environment=args.environment)
    elif args.action == 'checkpoint':
        value = controller.checkpoint(args.experiment, args.attempt, args.directory, request_id=args.request_id, source_resource=args.source_resource)
    elif args.action == 'recover':
        value = controller.recover(args.source, args.intent, args.directory, environment=args.environment)
    elif args.action == 'start':
        value = controller.start(args.experiment, deployment=args.deployment)
    elif args.action == 'continue-pre-reserve':
        from .runner import continue_pre_reserve
        value = continue_pre_reserve(args.attempt_directory)
    elif args.action == 'continue-input-upload':
        from .runner import continue_input_upload
        value = continue_input_upload(args.attempt_directory)
    elif args.action == 'confirm-start-binding':
        from .runner import confirm_start_binding
        value = confirm_start_binding(args.attempt_directory)
    elif args.action in {'status', 'monitor', 'wait'}:
        value = controller.status(args.experiment)
        if args.action == 'wait':
            deadline = time.monotonic() + min(60, max(0, args.timeout))
            while value.get('controller', {}).get('phase') == 'running' and time.monotonic() < deadline:
                time.sleep(min(2, max(0, deadline - time.monotonic())))
                value = controller.status(args.experiment)
        if not args.json:
            print(controller.render(value))
            return 0
    elif args.action == 'control':
        if (args.command == 'repair-ready') != (args.service is not None):
            parser.error('repair-ready requires --service; other controls do not accept it')
        value = controller.control(args.experiment, args.attempt, args.command, request_id=args.request_id,
                                   parameters={'service': args.service} if args.service else None)
    elif args.action == 'stop-evidence':
        value = controller.stop_evidence(args.experiment, args.attempt, args.output)
    elif args.action == 'import-source-stop':
        from .backends import import_source_stop
        value = import_source_stop(args.birth, args.status, args.output, args.identity_output,
                                   args.authorization, args.cancel_evidence,
                                   experiment=args.experiment, attempt_id=args.attempt)
    elif args.action == 'import-docker-source-stop':
        from .backends import import_docker_source_stop
        value = import_docker_source_stop(args.birth, args.status, args.writers, args.output, args.identity_output, args.authorization)
    elif args.action == 'retry':
        value = controller.retry(args.experiment, args.attempt, args.authorization, request_id=args.request_id)
    elif args.action == 'authority-handoff':
        from .admission import handoff
        value = handoff(read(args.endpoint), args.writer, args.registry, args.output, args.authorization,
                        mode=args.mode, scope=args.scope)
    elif args.action == 'telemetry':
        from . import telemetry
        if args.telemetry_action == 'snapshot':
            value = telemetry.snapshot(args.attempt)
        elif args.telemetry_action == 'batches':
            value = telemetry.batches(args.attempt, args.after, args.until)
        elif args.telemetry_action == 'export':
            value = telemetry.export(args.attempt, args.output, args.after, args.until)
        else:
            value = telemetry.ingest(args.output, args.transport)
    elif args.action == 'analyze':
        from .analyze import snapshot
        value = snapshot(args.experiment, args.output)
    elif args.action == 'history':
        value = history.inspect(args.source)
    elif args.action == 'artifact':
        if args.artifact_action == 'import':
            value = artifacts.import_evidence(args.store, args.source, evidence_type=args.type,
                     provenance=read(args.provenance) if args.provenance else None)
            if args.output:
                atomic(args.output, value)
        elif args.artifact_action == 'verify':
            value = artifacts.verify(args.store, read(args.reference))
        elif args.artifact_action == 'transfer':
            value = artifacts.transfer(args.source_store, args.store, read(args.reference))
        else:
            result = artifacts.materialize(args.store, read(args.reference), args.output)
            value = {'output': str(result), 'reference': read(args.reference)}
    else:
        path = artifacts.resolve(args.store, read(args.reference), args.member)
        if not path.is_file() or args.offset < 0 or not 1 <= args.bytes <= 262144:
            parser.error('evidence needs a regular file, nonnegative offset and 1..262144 bytes')
        with path.open('rb') as stream:
            stream.seek(args.offset)
            data = stream.read(args.bytes)
        value = {'reference': read(args.reference), 'member': args.member, 'offset': args.offset,
                 'next_offset': args.offset + len(data), 'content': data.decode(errors='replace'),
                 'truncated': args.offset + len(data) < path.stat().st_size}
    print(json.dumps(public(value), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
