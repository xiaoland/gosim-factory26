"""Run-oriented ARC execution and observation commands."""
import argparse
import json
import sys


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
    wait = commands.add_parser("wait")
    wait.add_argument("run")
    wait.add_argument("--json", action="store_true")
    logs = commands.add_parser("logs")
    logs.add_argument("run")
    logs.add_argument("--follow", action="store_true")
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("run")
    evaluate.add_argument("--kind", choices=("simulate", "official", "task"), required=True)
    evaluate.add_argument("--snapshot")
    archive = commands.add_parser("archive", help="只隐藏列表，不停止或删除运行")
    archive.add_argument("run")
    archive.add_argument("--undo", action="store_true")
    serve = commands.add_parser("serve")
    serve.add_argument("--config", required=True)
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
            value = run.status(args.run, include_all=args.all)
            if not args.json:
                from .status import render_runs
                print(render_runs(value if isinstance(value, list) else [value]))
                return 0
        elif args.command == "wait":
            value = run.wait(args.run)
            if not args.json:
                from .status import render_runs
                print(render_runs([value]))
                return 0
        elif args.command == "logs":
            run.logs(args.run, follow=args.follow)
            return 0
        elif args.command == "evaluate":
            value = run.evaluate(args.run, kind=args.kind, snapshot=args.snapshot)
        else:
            value = run.archive(args.run, undo=args.undo)
        print(json.dumps(value, ensure_ascii=False, default=str, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        detail = getattr(exc, "detail", None)
        if detail is not None:
            print(json.dumps(detail, ensure_ascii=False, default=str), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
