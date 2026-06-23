"""``solutionctl solution`` — discover solutions via the engine binary.

Resolves the engine binary and drives its headless ``solution`` subcommands:

* ``solution list``         → ``<bin> solution list``
* ``solution show <id>``    → ``<bin> solution show <id> [--lang ...]``

The engine already emits JSON on stdout, so we pass it through verbatim and
forward the engine's exit code. Zero engine code lives here — this module only
locates the binary and runs it as a subprocess (same pattern as ``deploy.py``).
"""

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional

from .._env import engine_env
from ..engine_locator import locate_engine


def _run_engine(args: List[str], solutions_dir: Optional[str] = None) -> int:
    """Run ``<engine> <args...>``, stream stdout through, forward exit code.

    The engine reads its solutions/devices dirs from the environment
    (``PS_SOLUTIONS_DIR`` / ``PS_DEVICES_DIR``), derived by :func:`engine_env`,
    so a fresh clone is auto-discovered. We deliberately do NOT pass
    ``--solutions-dir`` on the command line: the engine's ``--solutions-dir`` is
    a *top-level* flag (before the subcommand), and appending it after
    ``solution list`` makes argparse exit 2.
    """
    engine = locate_engine()
    print(f"Using engine: {engine}", file=sys.stderr)

    cmd = [str(engine), *args]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        env=engine_env(solutions_dir),
    )
    # Engine already prints JSON; pass it through unchanged.
    sys.stdout.write(proc.stdout)
    if proc.stdout and not proc.stdout.endswith("\n"):
        sys.stdout.write("\n")
    return proc.returncode


def run_list(solutions_dir: Optional[str] = None) -> int:
    """List available solutions (``<bin> solution list``)."""
    return _run_engine(["solution", "list"], solutions_dir=solutions_dir)


def run_show(
    solution_id: str,
    lang: Optional[str] = None,
    solutions_dir: Optional[str] = None,
) -> int:
    """Show one solution's detail incl. presets (``<bin> solution show <id>``)."""
    args = ["solution", "show", solution_id]
    if lang:
        args += ["--lang", lang]
    return _run_engine(args, solutions_dir=solutions_dir)
