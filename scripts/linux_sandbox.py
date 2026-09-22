"""Linux 参赛文件隔离：使用 Landlock ABI 3，限制由所有子进程继承。"""
import argparse
import ctypes
import os
from pathlib import Path
import platform


READ = (1 << 0) | (1 << 2) | (1 << 3)
ALL = (1 << 15) - 1  # ABI 3 includes REFER and TRUNCATE.
FILE = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 14)


class Ruleset(ctypes.Structure):
    _fields_ = [('handled_access_fs', ctypes.c_uint64)]


class Beneath(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]


def restrict(readonly, writable):
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'aarch64'):
        raise RuntimeError('参赛隔离要求 Linux x86_64/aarch64 与 Landlock ABI >= 3')
    libc = ctypes.CDLL(None, use_errno=True)
    def checked(result):
        if result < 0:
            number = ctypes.get_errno()
            raise OSError(number, 'Landlock 隔离失败：' + os.strerror(number))
        return result
    abi = checked(libc.syscall(444, 0, 0, 1))
    if abi < 3:
        raise RuntimeError('Landlock ABI < 3，无法保护需求截断；拒绝启动 Agent')
    ruleset = Ruleset(ALL)
    fd = checked(libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0))
    try:
        for names, rights in ((readonly, READ), (writable, ALL)):
            for name in names:
                path = Path(name).resolve(strict=True)
                handle = os.open(path, os.O_PATH | os.O_CLOEXEC)
                try:
                    rule = Beneath(rights if path.is_dir() else rights & FILE, handle)
                    checked(libc.syscall(445, fd, 1, ctypes.byref(rule), 0))
                finally:
                    os.close(handle)
        checked(libc.prctl(38, 1, 0, 0, 0))  # PR_SET_NO_NEW_PRIVS
        checked(libc.syscall(446, fd, 0))
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--read', action='append', default=[])
    parser.add_argument('--write', action='append', default=[])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('需要执行命令')
    # Chromium needs its own proc files. Landlock's domain hierarchy still
    # denies ptrace-sensitive files of the unsandboxed parent.
    system = ['/usr', '/bin', '/sbin', '/lib', '/lib64', '/etc', '/proc']
    devices = ['/dev/null', '/dev/urandom', '/dev/random', '/dev/tty']
    restrict([p for p in system if Path(p).exists()] + args.read,
             [p for p in devices if Path(p).exists()] + args.write)
    os.execvpe(command[0], command, os.environ)


if __name__ == '__main__':
    main()
