"""Freeze Docker CLI selection without introducing a machine registry."""

import json
import os
import subprocess
from pathlib import Path

SELECTION_ENV = ("DOCKER_CONTEXT", "DOCKER_HOST", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")


def environment(endpoint):
    env = dict(os.environ)
    for name in SELECTION_ENV:
        env.pop(name, None)
    env.pop("DOCKER_API_VERSION", None)
    env.update(endpoint.get("environment", {}))
    env["DOCKER_HOST"] = endpoint["host"]
    if "--tlsverify" in endpoint["argv"]:
        env["DOCKER_TLS_VERIFY"] = "1"
    elif "--tls" in endpoint["argv"]:
        env["DOCKER_TLS"] = "1"
    if "--tlscert" in endpoint["argv"]:
        env["DOCKER_CERT_PATH"] = str(Path(endpoint["argv"][endpoint["argv"].index("--tlscert") + 1]).parent)
    return env


def freeze(context=None):
    context = context or os.environ.get("DOCKER_CONTEXT")
    host = None if context else os.environ.get("DOCKER_HOST")
    argv = ["docker"]
    if not host:
        context = context or subprocess.check_output(["docker", "context", "show"], text=True).strip()
        value = json.loads(subprocess.check_output(["docker", "context", "inspect", context], text=True))[0]
        settings = value["Endpoints"]["docker"]
        host = settings["Host"]
        material = value.get("TLSMaterial", {}).get("docker", [])
        if material:
            argv.append("--tls" if settings.get("SkipTLSVerify") else "--tlsverify")
            for name, flag in (("ca.pem", "--tlscacert"), ("cert.pem", "--tlscert"), ("key.pem", "--tlskey")):
                if name in material:
                    argv += [flag, str(Path(value["Storage"]["TLSPath"]) / "docker" / name)]
    else:
        if os.environ.get("DOCKER_TLS_VERIFY"):
            argv.append("--tlsverify")
        elif os.environ.get("DOCKER_TLS"):
            argv.append("--tls")
        if "--tlsverify" in argv or "--tls" in argv:
            root = Path(os.environ.get("DOCKER_CERT_PATH", Path.home() / ".docker")).expanduser()
            for name, flag in (("ca.pem", "--tlscacert"), ("cert.pem", "--tlscert"), ("key.pem", "--tlskey")):
                argv += [flag, str(root / name)]
    argv += ["--host", host]
    endpoint = {"schema_version": 1, "context": context, "host": host, "argv": argv,
                "remote": not host.startswith(("unix://", "npipe://")),
                "environment": {"DOCKER_CONFIG": str(Path(os.environ.get("DOCKER_CONFIG", Path.home() / ".docker")).expanduser()),
                                **({"DOCKER_API_VERSION": os.environ["DOCKER_API_VERSION"]}
                                   if os.environ.get("DOCKER_API_VERSION") else {})}}
    endpoint["daemon_id"] = subprocess.check_output(
        argv + ["info", "--format", "{{.ID}}"], env=environment(endpoint), text=True, timeout=15).strip()
    if not endpoint["daemon_id"]:
        raise ValueError("Docker did not return a daemon ID")
    return endpoint


def confirm(endpoint):
    identity = subprocess.check_output(endpoint["argv"] + ["info", "--format", "{{.ID}}"],
                                       env=environment(endpoint), text=True, stderr=subprocess.STDOUT,
                                       timeout=10).strip()
    if identity != endpoint["daemon_id"]:
        raise ValueError(f"Docker daemon identity changed: {identity!r} != {endpoint['daemon_id']!r}")


def execute(endpoint, args, **kwargs):
    return subprocess.run(endpoint["argv"] + args, env=environment(endpoint), **kwargs)
