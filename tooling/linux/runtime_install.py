"""Install the small public runtime immediately before a Harness starts.

The submitted package carries the native executables, lock files and patches;
the container supplies the ordinary Node/Python system and writable cache.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

try:
    from tooling.linux.browser_runtime import browser_scripts
except ModuleNotFoundError:  # packaged entry: helper is copied beside this file
    from browser_runtime import browser_scripts

NODE_PACKAGE = "node-linux-x64@24.10.0"


def application_environment(runtime: Path, environment: dict[str, str],
                            tool_paths: tuple[Path, ...] = ()) -> dict[str, str]:
    """Use the platform application Node without exposing the tools' Node."""
    result = dict(environment)
    result.pop("NODE_PATH", None)
    # Unix socket paths include the session name; durable run paths are too long.
    socket_scope = result.get("AGENT_BROWSER_SOCKET_DIR", str(runtime))
    socket_root = Path("/tmp/f26-b") if sys.platform == "linux" else Path("/Volumes/WorkSSD/.factory26/browser-sockets")
    result["AGENT_BROWSER_SOCKET_DIR"] = str(socket_root / hashlib.sha256(socket_scope.encode()).hexdigest()[:12])
    result["PATH"] = os.pathsep.join(map(str, (
        Path("/usr/local/bin"), *tool_paths, runtime / "tools", Path("/usr/bin"), Path("/bin"))))
    return result


def _tool_launchers(runtime: Path) -> None:
    directory = runtime / "tools"
    directory.mkdir(exist_ok=True)
    for name in ("pi", "braid", "agent-browser", "browser-install", "browser-exec"):
        executable = runtime / "bin" / name
        if executable.is_file():
            launcher = directory / name
            launcher.unlink(missing_ok=True)
            launcher.write_text('#!/bin/sh\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                                + f'exec "$HERE/../bin/{name}" "$@"\n')
            launcher.chmod(0o755)
    for name in ("playwright", "mcporter", "portless"):
        entry = (runtime / "node_modules/.bin" / name).resolve(strict=True)
        launcher = directory / name
        launcher.write_text('#!/bin/sh\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                            + 'exec "$HERE/../bin/node" "$HERE/../'
                            + str(entry.relative_to(runtime)) + '" "$@"\n')
        launcher.chmod(0o755)


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _repair_background_bash(path: Path) -> None:
    """Apply the managed-launch hunk when upstream line context drifted."""
    text = path.read_text()
    old = '\t\tconst child = spawn("bash", ["-lc", params.command], {\n\t\t\tcwd,\n\t\t\tenv: process.env,\n\t\t\tdetached: true,\n\t\t\tstdio: ["ignore", "pipe", "pipe"],\n\t\t});'
    new = '\t\tconst managedRuntime = (globalThis as any)[Symbol.for("factory26.native-runtime.v1")];\n\t\tlet child: ChildProcess;\n\t\tlet managedStartup: Promise<unknown> | undefined;\n\t\ttry {\n\t\tchild = (managedRuntime?.spawnManaged ?? spawn)("bash", ["-lc", params.command], {\n\t\t\tcwd,\n\t\t\tenv: process.env,\n\t\t\tdetached: true,\n\t\t\tstdio: ["ignore", "pipe", "pipe"],\n\t\t}, { kind: "tool", service: job.service, manifest: job.pbb ? join(pbbJobsDir(job.pbb), `${job.id}.json`) : undefined });\n\t\tmanagedStartup = managedRuntime?.waitManagedStartup(child);\n\t\t} catch (error) {\n\t\t\tjob.startError = error instanceof Error ? error.message : String(error);\n\t\t\tfinish({ status: "error", error, body: job.startError, details: undefined, outcome: "error", exitCode: null });\n\t\t\treturn;\n\t\t}'
    if old not in text:
        raise RuntimeError(f"managed background-bash hunk has unexpected source: {path}")
    path.write_text(text.replace(old, new, 1))


def ensure(root: str | Path) -> Path:
    root = Path(root).resolve()
    runtime = root / "runtime"
    marker = runtime / ".factory26-installed.json"
    if marker.is_file():
        _tool_launchers(runtime)
        return runtime
    runtime.mkdir(parents=True, exist_ok=True)
    (root / ".cache").mkdir(parents=True, exist_ok=True)
    native = root / "native"
    for name in ("pi", "braid", "tini"):
        source = native / "bin" / name
        if source.is_file():
            target = runtime / "bin" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            target.chmod(0o755)
    managed = native / "native-managed.mjs"
    if managed.is_file():
        shutil.copy2(managed, runtime / "native-managed.mjs")

    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("public ARC package requires npm in the container image")
    target = runtime / "bin/node"
    target.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "linux":
        with tempfile.TemporaryDirectory(prefix="factory26-node-", dir=root / ".cache") as temporary:
            bootstrap = Path(temporary)
            _run([npm, "install", "--prefix", str(bootstrap), "--ignore-scripts", "--no-save",
                  "--no-audit", "--no-fund", NODE_PACKAGE])
            source = next(bootstrap.glob("node_modules/node-linux-x64/**/bin/node"), None)
            if source is None:
                raise RuntimeError("node-linux-x64 installed but did not provide bin/node")
            shutil.copy2(source, target)
            target.chmod(0o755)
    else:
        raise RuntimeError("the submitted ARC package requires a Linux container; Mac only assembles it")

    npm_source = root / "inputs/npm"
    if not (npm_source / "package-lock.json").is_file():
        raise RuntimeError("public ARC package is missing inputs/npm/package-lock.json")
    shutil.copy2(npm_source / "package.json", runtime / "package.json")
    shutil.copy2(npm_source / "package-lock.json", runtime / "package-lock.json")
    env = dict(os.environ)
    env["PATH"] = str(runtime / "bin") + os.pathsep + env.get("PATH", "")
    _run([npm, "ci", "--ignore-scripts", "--legacy-peer-deps", "--no-audit",
          "--no-fund", "--prefix", str(runtime)], env=env)

    patches = json.loads((npm_source / "native-patches.json").read_text())
    patch_root = npm_source / "patches"
    patch = shutil.which("patch")
    if not patch:
        raise RuntimeError("public ARC package requires patch in the container image")
    for item in patches:
        command = [patch, "--batch", "--fuzz=3", "-p1", "-d", str(runtime / "node_modules" / item["package"]),
                   "-i", str(patch_root / item["file"])]
        result = subprocess.run(command)
        if result.returncode and item["file"] == "pi-background-bash-1.0.5-i13-2-managed.patch":
            _repair_background_bash(runtime / "node_modules/pi-background-bash/extensions/background-bash.ts")
            (runtime / "node_modules/pi-background-bash/extensions/background-bash.ts.rej").unlink(missing_ok=True)
        elif result.returncode:
            raise subprocess.CalledProcessError(result.returncode, command)
    # Keep the normal container PATH independent of npm's implementation detail.
    # These links are the public entry points used by the Harness and by the
    # browser helper; the package itself remains under runtime/node_modules.
    bin_dir = runtime / "bin"
    for name in ("agent-browser", "playwright", "mcporter", "portless", "pnpm"):
        source = runtime / "node_modules" / ".bin" / name
        if source.exists():
            link = bin_dir / name
            link.unlink(missing_ok=True)
            link.symlink_to(source)
    for name, script in browser_scripts().items():
        path = bin_dir / name
        # agent-browser is also an npm .bin entry.  Never follow that link
        # when materialising the public wrapper: doing so would overwrite the
        # upstream JavaScript launcher with shell source.
        path.unlink(missing_ok=True)
        path.write_text(script)
        path.chmod(0o755)
    _tool_launchers(runtime)
    marker.write_text(json.dumps({"node": NODE_PACKAGE, "installed": True}) + "\n")
    return runtime
