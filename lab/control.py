"""Physical process identity and read-only historical change waiting.

Current run control belongs to its execution adapter, not a controller socket.
"""

import ctypes
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

from .records import read_json


def boot_id():
    if sys.platform == "darwin":
        return subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "kern.bootsessionuuid"], text=True, timeout=5).strip()
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


class _ProcBsdInfo(ctypes.Structure):
    # Darwin sys/proc_info.h: PROC_PIDTBSDINFO, including microsecond birth time.
    _fields_ = [("ids", ctypes.c_uint32 * 12), ("comm", ctypes.c_char * 16),
                ("name", ctypes.c_char * 32), ("files_and_group", ctypes.c_uint32 * 5),
                ("nice", ctypes.c_int32), ("start_sec", ctypes.c_uint64),
                ("start_usec", ctypes.c_uint64)]


def process_start(pid):
    if sys.platform == "darwin":
        info = _ProcBsdInfo()
        library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        query = library.proc_pidinfo
        query.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
                          ctypes.c_void_p, ctypes.c_int]
        query.restype = ctypes.c_int
        size = query(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
        if size != ctypes.sizeof(info):
            error = ctypes.get_errno()
            raise OSError(error, f"proc_pidinfo({pid}) returned {size} bytes")
        return f"{info.start_sec}.{info.start_usec:06d}"
    return Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()[19]


def process_identity(pid=None):
    """Read local host, boot and process birth identity; retain unavailable facts."""
    pid = os.getpid() if pid is None else pid
    record = {"host": socket.gethostname(), "boot_id": None, "pid": pid,
              "process_start": None}
    try:
        record["boot_id"] = boot_id()
    except (OSError, subprocess.SubprocessError) as exc:
        record["boot_error"] = f"{type(exc).__name__}: {exc}"
    if type(pid) is not int or not 0 < pid <= 2**31 - 1:
        record["process_error"] = "pid must be a positive signed 32-bit integer"
        return record
    try:
        record["process_start"] = process_start(pid)
    except (OSError, ValueError, IndexError) as exc:
        record["process_error"] = f"{type(exc).__name__}: {exc}"
    return record


def process_state(record):
    """Return alive/lost/unknown without treating missing birth facts as identity."""
    if not record or record.get("host") != socket.gethostname():
        return "unknown"
    pid = record.get("pid")
    if type(pid) is not int or not 0 < pid <= 2**31 - 1:
        return "unknown"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "lost"
    except OSError:
        return "unknown"
    current = process_identity(pid)
    if not record.get("boot_id") or not current.get("boot_id") or record["boot_id"] != current["boot_id"]:
        return "unknown"
    if not record.get("process_start") or not current.get("process_start"):
        return "unknown"
    return "alive" if record["process_start"] == current["process_start"] else "lost"


def owner_state(record):
    return process_state(record)


def wait_for_change(experiment, after=0):
    experiment = Path(experiment)
    owner = read_json(experiment / "active.json")
    state = owner_state(owner)
    if state != "alive" or owner.get("phase") != "running":
        return {"closed": state == "lost" or owner.get("phase") == "finished",
                "owner_state": state, "controller_id": owner.get("controller_id"), "events": after}
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(65)
        connection.connect(owner["socket"])
        connection.sendall(json.dumps({"action": "wait", "after": after}).encode())
        return json.loads(connection.recv(65536))
