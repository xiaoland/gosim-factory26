"""Local controller ownership, operation socket and durable change feed."""

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
from queue import Empty, Queue
import secrets
import socket
from threading import Condition, Event, Thread
import time

from .records import read_json, write_json


def boot_id():
    path = Path("/proc/sys/kernel/random/boot_id")
    return path.read_text().strip() if path.is_file() else None


def process_start(pid):
    path = Path(f"/proc/{pid}/stat")
    if not path.is_file():
        return None
    return path.read_text().rsplit(") ", 1)[1].split()[19]


def owner_state(record):
    if not record:
        return "unknown"
    if record.get("host") != socket.gethostname() or record.get("boot_id") != boot_id():
        return "unknown"
    return "alive" if process_start(record.get("pid")) == record.get("process_start") else "lost"


@contextmanager
def exclusive(experiment):
    lock = Path(experiment) / "controller.lock"
    with lock.open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"experiment already has an active controller: {experiment}") from exc
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
        self.record = {"controller_id": self.id, "host": socket.gethostname(), "boot_id": boot_id(),
                       "pid": os.getpid(), "process_start": process_start(os.getpid()),
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
    if owner_state(owner) != "alive" or owner.get("phase") != "running":
        return {"closed": True, "controller_id": owner.get("controller_id"), "events": after}
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(65)
        connection.connect(owner["socket"])
        connection.sendall(json.dumps({"action": "wait", "after": after}).encode())
        return json.loads(connection.recv(65536))
