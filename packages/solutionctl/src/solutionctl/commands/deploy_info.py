"""``solutionctl deploy-info`` — show how to deploy a solution.

Forwards to the engine's ``deploy-info`` headless subcommand, which returns
(as JSON): the available presets, the required connection parameters per
deployment step, the local/remote target options, and a ready-to-fill
``request_template`` connection skeleton. The agent reads this, fills in the
``--connection`` JSON, and calls ``solutionctl deploy``.

Zero engine code lives here — this module only locates the binary and runs it
as a subprocess (same pattern as ``solution.py`` / ``deploy.py``), passing the
auto-derived engine environment so a fresh clone's ``solutions/`` is used.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Optional

from .._env import engine_env
from ..engine_locator import locate_engine


def run(
    solution_id: str,
    preset: Optional[str] = None,
    lang: Optional[str] = None,
    solutions_dir: Optional[str] = None,
) -> int:
    """Run ``<engine> deploy-info <id> [--preset] [--lang]``; pass JSON through."""
    engine = locate_engine()
    print(f"Using engine: {engine}", file=sys.stderr)

    cmd = [str(engine), "deploy-info", solution_id]
    if preset:
        cmd += ["--preset", preset]
    if lang:
        cmd += ["--lang", lang]

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        env=engine_env(solutions_dir),
    )
    sys.stdout.write(proc.stdout)
    if proc.stdout and not proc.stdout.endswith("\n"):
        sys.stdout.write("\n")
    return proc.returncode
