"""Local controller ownership, operation socket and durable change feed."""

from contextlib import contextmanager
import ctypes
import fcntl
import json
import os
from pathlib import Path
from queue import Empty, Queue
import secrets
import socket
import subprocess
import sys
from threading import Condition, Event, Thread
import time

from .records import read_json, write_json


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


@contextmanager
def exclusive(experiment):
    lock = Path(experiment) / "controller.lock"
    with lock.open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"experiment already has an active controller: {experiment}") from exc
        active = Path(experiment) / "active.json"
        if active.is_file():
            previous = read_json(active)
            if previous.get("phase") == "running" and owner_state(previous) != "lost":
                raise RuntimeError(f"previous controller exit is unconfirmed: {experiment}")
        yield


class Control:
    def __init__(self, experiment):
        self.experiment = Path(experiment)
        self.id = f"controller-{secrets.token_hex(6)}"
        self.root = self.experiment / "controllers" / self.id
        self.root.mkdir(parents=True)
        (self.root / "operations").mkdir()
        self.runtime = Path("/tmp") / f"lab-{secrets.token_hex(8)}"
        self.runtime.mkdir(mode=0o700)
        self.socket_path = self.runtime / "control.sock"
        self.commands = Queue()
        self.changed = Condition()
        self.events = 0
        self.closed = Event()
        self.record = {"controller_id": self.id, **process_identity(),
                       "socket": str(self.socket_path), "started_at": time.time(), "phase": "running"}
        write_json(self.root / "controller.json", self.record)
        write_json(self.experiment / "active.json", self.record)
        self.server = socket.socket(socket.AF_UNIX)
        self.server.bind(str(self.socket_path))
        os.chmod(self.socket_path, 0o600)
        self.server.listen(16)
        self.server.settimeout(1)
        self.thread = Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while not self.closed.is_set():
            try:
                conn, _ = self.server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        with conn:
            try:
                request = json.loads(conn.recv(65536))
                if request.get("action") == "wait":
                    after = request.get("after", 0)
                    with self.changed:
                        self.changed.wait_for(lambda: self.events > after or self.closed.is_set(), timeout=60)
                    response = {"events": self.events, "controller_id": self.id,
                                "closed": self.closed.is_set()}
                else:
                    response_queue = Queue(maxsize=1)
                    self.commands.put((request, response_queue))
                    response = response_queue.get(timeout=45)
                conn.sendall(json.dumps(response).encode())
            except (OSError, ValueError, TimeoutError, Empty) as exc:
                try:
                    conn.sendall(json.dumps({"error": f"{type(exc).__name__}: {exc}"}).encode())
                except OSError:
                    pass

    def emit(self, kind, **values):
        with self.changed:
            self.events += 1
            event = {"controller_id": self.id, "seq": self.events, "time": time.time(),
                     "kind": kind, **values}
            with (self.root / "notifications.jsonl").open("a") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            self.changed.notify_all()
        return event

    def finish(self):
        self.record.update(phase="finished", finished_at=time.time())
        write_json(self.root / "controller.json", self.record)
        write_json(self.experiment / "active.json", self.record)
        self.closed.set()
        with self.changed:
            self.changed.notify_all()
        self.server.close()
        self.thread.join(timeout=2)
        self.socket_path.unlink(missing_ok=True)
        self.runtime.rmdir()


def send(experiment, action, **values):
    experiment = Path(experiment)
    owner = read_json(experiment / "active.json")
    if owner_state(owner) != "alive" or owner.get("phase") != "running":
        raise RuntimeError(f"controller is not confirmed active: {experiment}")
    identifier = secrets.token_hex(12)
    operation = {"id": identifier, "action": action, **values}
    directory = experiment / "controllers" / owner["controller_id"] / "operations"
    write_json(directory / f"{identifier}.request.json", operation)
    try:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(50)
            connection.connect(owner["socket"])
            connection.sendall(json.dumps({"id": identifier}).encode())
            reply = json.loads(connection.recv(65536))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"operation {identifier} outcome unknown; inspect its saved request/result") from exc
    if reply.get("error"):
        raise RuntimeError(f"operation {identifier}: {reply['error']}; inspect its saved request/result")
    return reply


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
