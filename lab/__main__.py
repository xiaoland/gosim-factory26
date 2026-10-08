"""Run-oriented ARC execution and observation commands."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def _print_saved(path):
    receipt = Path(path) / "records/result-save.json"
    if not receipt.is_file():
        print(f"saved=unknown receipt={receipt}")
        return
    try:
        value = json.loads(receipt.read_text())
        print(json.dumps({key: value[key] for key in ("saved", "scope", "gaps", "errors", "as_of")
                          if key in value}, ensure_ascii=False, default=str, separators=(",", ":")))
    except (OSError, ValueError, TypeError) as exc:
        print(f"saved=unknown receipt={receipt} error={type(exc).__name__}: {exc}")


def _print_result(command, value, args, run):
    from .status import render_runs
    if command == "save":
        print(f"package={value.get('package', '-')}")
        print(f"lifecycle={value.get('lifecycle', 'unknown')} consistent={value.get('consistent')}")
        print(f"source_as_of={value.get('source_as_of', '-')}")
        print(f"packaged_at={value.get('packaged_at', value.get('as_of', '-'))}")
        print(f"members={json.dumps(value.get('members', {}), ensure_ascii=False, separators=(',', ':'))}")
        excluded = value.get("excluded") or []
        gaps = value.get("gaps") or []
        errors = value.get("errors") or []
        print(f"excluded={len(excluded)} gaps={json.dumps(gaps, ensure_ascii=False, separators=(',', ':'))}")
        print(f"errors={json.dumps(errors, ensure_ascii=False, separators=(',', ':'))}")
        print(f"records={Path(value.get('source_run', args.run)) / 'records'}")
        return
    if command in ("stop", "pause", "resume"):
        print(f"run={args.run} action={command}")
        receipt = {key: value[key] for key in (
            "action", "container_id", "commands", "as_of", "observed_at", "lifecycle", "error"
        ) if key in value}
        print(json.dumps(receipt, ensure_ascii=False, default=str, separators=(",", ":")))
        _print_saved(run.resolve(args.run))
        return
    row = run.status(value["run_id"]) if command == "evaluate" else value
    rows = row if isinstance(row, list) else [row]
    print(render_runs(rows))
    for item in rows:
        if item.get("error"):
            print(f"error[{item['run_id']}]: {item['error']}")
    if isinstance(row, list):
        return
    if command in ("start", "restart", "status", "wait"):
        target = row.get("target_config") or {}
        recipe = row.get('model_recipe') or target.get('model_recipe') or target.get('model_transport', 'unknown')
        print(f"recipe={recipe} competition={row.get('competition')}"
              f" source={row.get('source_run') or '-'}")
        usage = (row.get('spend') or {}).get('usage') or {}
        totals = [item.get('tokens', {}).get('totalTokens') for item in usage.get('items', [])]
        known = [value for value in totals if value is not None]
        if known:
            print(f"native_tokens={sum(known)} scope={usage.get('scope')} coverage={usage.get('status')}"
                  "；原生用量不等于供应商账单")
        provider_usage = (row.get('spend') or {}).get('provider_usage') or {}
        attempts = provider_usage.get('attempts') or []
        if attempts:
            channels = list(dict.fromkeys(item.get('deployment_id') for item in attempts))
            returned = sum(item.get('usage_status') == 'recorded' for item in attempts)
            print(f"provider_attempts={len(attempts)} returned_usage={returned}"
                  f" deployments={','.join(str(value) for value in channels)}；不是账单或套餐余额")
        restart_summary = row.get("restart_summary") or {}
        if restart_summary.get("is_restart"):
            material = restart_summary.get("material") or {}
            requests = restart_summary.get("actual_requests") or {}
            observation = restart_summary.get("variant_observation") or {}
            action = observation.get("effective_action") or {}
            saved_material = material.get("saved")
            saved_ok = (saved_material.get("saved")
                        if isinstance(saved_material, dict) else saved_material is True)
            consumed = material.get("consumed") or {}
            frozen = material.get("frozen") or {}
            print(f"restart_source={restart_summary.get('source_run') or '-'}"
                  f" material_saved={saved_ok}"
                  f" native_resume={material.get('native_resume')}"
                  f" frozen_program={frozen.get('program_version') or '-'}"
                  f" consumed_adopted={consumed.get('adopted')}"
                  f" requests={requests.get('count', 0)}"
                  f" responses={requests.get('responses', 0)}"
                  f" successful_responses={requests.get('successful_responses', 0)}"
                  f" scope={requests.get('scope')}"
                  f" activity={observation.get('activity') or 'unknown'}"
                  f" action_tool={action.get('tool') or '-'}"
                  f" action_outcome={action.get('outcome') or '-'}"
                  f" action_at={observation.get('action_at') or '-'}"
                  f" action_valid={observation.get('valid')}")
    elif command == "archive":
        print(f"archived={row['archived']}")
    elif command == "evaluate":
        print(f"evaluation={value['evaluation_kind']} source={value['source_run']}"
              f" snapshot={row.get('application_snapshot', 'unknown')}")
        print("评测已派发；是否完成及实际评分以保存的评测结果为准。")
    print(f"records={row['path']}/records")
    _print_saved(row["path"])


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lab", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start", help="组装并直接启动一次运行")
    start.add_argument("variant")
    start.add_argument("target")
    start.add_argument("task")
    start.add_argument("--route")
    start.add_argument("--competition", action="store_true")
    start.add_argument("--script")
    for name in ("stop", "pause", "resume"):
        commands.add_parser(name).add_argument("run")
    restart = commands.add_parser("restart", help="同 variant 迁移完整 data，启动新 run")
    restart.add_argument("run")
    for name in ("target", "task", "route", "snapshot"):
        restart.add_argument(f"--{name}")
    status = commands.add_parser("status", help="默认显示未归档且未正常完成的运行")
    status.add_argument("run", nargs="?")
    status.add_argument("--all", action="store_true")
    status.add_argument("--json", action="store_true")
    status.add_argument("--follow", action="store_true",
                        help="terminal run 后只跟随明确的 restart 后继")
    status.add_argument("--interval", type=float, default=10,
                        help="--follow 轮询间隔（秒）")
    wait = commands.add_parser("wait")
    wait.add_argument("run")
    wait.add_argument("--json", action="store_true")
    save = commands.add_parser("save", help="取得可搬运现场包，不停止运行")
    save.add_argument("run")
    save.add_argument("--output", help="目标 .zip 路径；默认写入 run/snapshots")
    save.add_argument("--json", action="store_true")
    logs = commands.add_parser("logs")
    logs.add_argument("run")
    logs.add_argument("--follow", action="store_true")
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("run")
    evaluate.add_argument("--kind", choices=("simulate", "official", "task", "self-test"), required=True)
    evaluate.add_argument("--snapshot")
    evaluate.add_argument("--task", help="评测题目别名；self-test 使用 github-stage-*-req-test")
    archive = commands.add_parser("archive", help="只隐藏列表，不停止或删除运行")
    archive.add_argument("run")
    archive.add_argument("--undo", action="store_true")
    serve = commands.add_parser("serve")
    serve.add_argument("--config", required=True)
    for name in ("start", "stop", "pause", "resume", "restart", "evaluate", "archive"):
        commands.choices[name].add_argument("--json", action="store_true", help="输出完整结构化回执")
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            from .serve import serve
            serve(args.config)
            return 0
        from . import run
        if args.command == "start":
            value = run.start(args.variant, args.target, args.task, route=args.route,
                              competition=args.competition, script=args.script)
        elif args.command in ("stop", "pause", "resume"):
            value = getattr(run, args.command)(args.run)
        elif args.command == "restart":
            value = run.restart(args.run, target=args.target, task=args.task,
                                route=args.route, snapshot=args.snapshot)
        elif args.command == "status":
            if args.follow:
                if not args.run:
                    raise ValueError("status --follow requires RUN")
                from .automation import watch
                from .status import render_runs
                for item in watch(args.run, interval=args.interval, follow=True):
                    if args.json:
                        print(json.dumps(item, ensure_ascii=False, default=str), flush=True)
                    else:
                        print(render_runs([item]), flush=True)
                        continuation = item.get("continuation") or {}
                        if continuation.get("label"):
                            print(f"continuation={continuation['label']}", flush=True)
                        summary = item.get("restart_summary") or {}
                        if summary.get("is_restart"):
                            material = summary.get("material") or {}
                            requests = summary.get("actual_requests") or {}
                            observation = summary.get("variant_observation") or {}
                            action = observation.get("effective_action") or {}
                            print("restart_summary=" + json.dumps({
                                "source_run": summary.get("source_run"),
                                "material_saved": ((material.get("saved") or {}).get("saved")
                                                    if isinstance(material.get("saved"), dict)
                                                    else material.get("saved") is True),
                                "consumed_adopted": (material.get("consumed") or {}).get("adopted"),
                                "requests": requests.get("count", 0),
                                "successful_responses": requests.get("successful_responses", 0),
                                "activity": observation.get("activity"),
                                "action_tool": action.get("tool"),
                                "action_outcome": action.get("outcome"),
                                "action_valid": observation.get("valid"),
                                "action_at": observation.get("action_at"),
                            }, ensure_ascii=False, separators=(",", ":")), flush=True)
                return 0
            value = run.status(args.run, include_all=args.all)
        elif args.command == "wait":
            value = run.wait(args.run)
        elif args.command == "save":
            value = run.save(args.run, output=args.output)
        elif args.command == "logs":
            run.logs(args.run, follow=args.follow)
            return 0
        elif args.command == "evaluate":
            configuration = ({"task": args.task, "platform_task": args.task}
                             if args.task else None)
            value = run.evaluate(args.run, kind=args.kind, snapshot=args.snapshot,
                                 configuration=configuration)
        else:
            value = run.archive(args.run, undo=args.undo)
        if args.json:
            print(json.dumps(value, ensure_ascii=False, default=str, indent=2))
        else:
            _print_result(args.command, value, args, run)
        if args.command == "save" and (value.get("source_saved") is not True or value.get("errors")):
            return 1
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        path = getattr(exc, "lab_run_path", None)
        if path:
            print(f"run={Path(path).name} records={path}/records", file=sys.stderr)
        detail = getattr(exc, "detail", None)
        if detail is not None:
            print(json.dumps(detail, ensure_ascii=False, default=str), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
