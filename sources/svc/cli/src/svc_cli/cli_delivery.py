"""Shared terminal delivery for resolved core-command results and errors."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TextIO, TypeVar

from .cli_output.model import MachineModel, dump_machine_output, project_error
from .errors import SvcError


ResultT = TypeVar("ResultT")


def deliver_result(
    result: ResultT,
    *,
    json_output: bool,
    project: Callable[[ResultT], MachineModel],
    render: Callable[[ResultT, TextIO], None],
    exit_code: int,
) -> int:
    """Deliver one resolved result to stdout through exactly one representation."""

    if json_output:
        dump_machine_output(project(result), sys.stdout)
    else:
        render(result, sys.stdout)
    return exit_code


def deliver_error(
    error: SvcError,
    *,
    json_output: bool,
    render: Callable[[SvcError, TextIO], None],
    exit_code: int,
) -> int:
    """Deliver one service/interface failure to stderr."""

    if json_output:
        dump_machine_output(project_error(error), sys.stderr)
    else:
        render(error, sys.stderr)
    return exit_code
