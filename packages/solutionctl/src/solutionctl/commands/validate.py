"""Offline ``validate`` command — engine-free solution checker.

Unlike ``deploy`` / ``manage`` / ``meta`` (which subprocess the engine binary),
``validate`` runs fully offline with zero engine dependency. It only uses:

* the contract files under ``spec/`` (``solution.schema.json``,
  ``device.schema.json``, ``capabilities.json``), and
* the ``sensecraft_solution_spec`` parser subpackage (guide.md parsing).

It never imports ``provisioning_station`` and never shells out to the engine.

Checks performed against ``<solution_path>``:

1. ``solution.yaml`` validated against ``spec/solution.schema.json``.
2. ``devices/*.yaml`` (if present) validated against ``spec/device.schema.json``.
3. ``guide.md`` (+ ``guide_zh.md`` if present) parsed with the valid step-type
   set seeded from ``capabilities.json`` deployer keys, surfacing parse errors
   and illegal ``type=`` values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# NOTE: jsonschema / yaml / sensecraft_solution_spec are declared deps. Engine
# packages (provisioning_station) are intentionally NOT imported anywhere here.


def _find_spec_dir(solution_path: Path, explicit: str | None) -> Path | None:
    """Locate the ``spec/`` directory holding ``solution.schema.json``.

    Resolution order:
    1. ``--spec-dir`` if given (must directly contain ``solution.schema.json``).
    2. Walk up from the solution path, then from cwd, looking for a ``spec/``
       subdirectory that contains ``solution.schema.json``.
    """
    marker = "solution.schema.json"

    if explicit:
        d = Path(explicit).expanduser().resolve()
        if (d / marker).is_file():
            return d
        return None

    seen: set[Path] = set()
    for start in (solution_path.resolve(), Path.cwd().resolve()):
        cur = start
        while cur not in seen:
            seen.add(cur)
            candidate = cur / "spec"
            if (candidate / marker).is_file():
                return candidate
            if cur.parent == cur:
                break
            cur = cur.parent
    return None


def _format_jsonschema_errors(validator_cls, instance, schema, label: str) -> list[str]:
    """Run a jsonschema validator and return human-readable error strings."""
    errors: list[str] = []
    for err in sorted(
        validator_cls(schema).iter_errors(instance), key=lambda e: list(e.absolute_path)
    ):
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"{label}: at '{path}': {err.message}")
    return errors


def run(solution_path: str, spec_dir: str | None = None) -> int:
    """Validate a single solution offline. Returns 0 on success, 1 on errors."""
    import jsonschema
    import yaml

    sol_path = Path(solution_path).expanduser()
    if not sol_path.is_dir():
        print(f"Error: solution path not found: {sol_path}", file=sys.stderr)
        return 1

    spec = _find_spec_dir(sol_path, spec_dir)
    if spec is None:
        hint = (
            f"--spec-dir '{spec_dir}' does not contain solution.schema.json"
            if spec_dir
            else "no spec/ directory with solution.schema.json found near the "
            "solution path or current directory"
        )
        print(f"Error: cannot locate contract files: {hint}", file=sys.stderr)
        print("Hint: pass --spec-dir pointing at the repo's spec/ directory.", file=sys.stderr)
        return 1

    errors: list[str] = []
    validator_cls = jsonschema.Draft202012Validator

    # --- 1. solution.yaml against solution.schema.json -----------------------
    sol_yaml = sol_path / "solution.yaml"
    if not sol_yaml.is_file():
        # Not a solution directory (e.g. shared assets like ``_shared/``, or a
        # container dir holding nested solutions). Skip rather than fail so
        # iterating ``solutions/*`` stays clean.
        print(f"⊘ {sol_path.name} skipped (no solution.yaml — not a solution directory)")
        return 0
    sol_data = None
    try:
        sol_data = yaml.safe_load(sol_yaml.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"solution.yaml: YAML parse error: {exc}")
    if sol_data is not None:
        sol_schema = json.loads((spec / "solution.schema.json").read_text(encoding="utf-8"))
        errors.extend(
            _format_jsonschema_errors(validator_cls, sol_data, sol_schema, "solution.yaml")
        )

    # --- 2. devices/*.yaml against device.schema.json ------------------------
    devices_dir = sol_path / "devices"
    if devices_dir.is_dir():
        dev_schema_path = spec / "device.schema.json"
        dev_schema = (
            json.loads(dev_schema_path.read_text(encoding="utf-8"))
            if dev_schema_path.is_file()
            else None
        )
        if dev_schema is None:
            errors.append("device.schema.json not found in spec/ — cannot validate devices/")
        else:
            for dev_file in sorted(devices_dir.glob("*.yaml")):
                label = f"devices/{dev_file.name}"
                try:
                    dev_data = yaml.safe_load(dev_file.read_text(encoding="utf-8"))
                except yaml.YAMLError as exc:
                    errors.append(f"{label}: YAML parse error: {exc}")
                    continue
                errors.extend(
                    _format_jsonschema_errors(validator_cls, dev_data, dev_schema, label)
                )

    # --- 3. guide step-type validation via the parser subpackage -------------
    caps_path = spec / "capabilities.json"
    if not caps_path.is_file():
        errors.append("capabilities.json not found in spec/ — cannot validate step types")
    else:
        from sensecraft_solution_spec import markdown_parser as mp

        caps = json.loads(caps_path.read_text(encoding="utf-8"))
        deployer_keys = set(caps.get("deployers", {}).keys())
        # Seed the parser's valid step-type set from the contract (engine-free).
        mp.register_step_type_provider(lambda: deployer_keys)

        # Resolve the guide path from solution.yaml's deployment.guide_file so
        # legacy solutions (e.g. guide under deploy/) validate correctly; fall
        # back to the flat-layout default guide.md.
        guide_rel = "guide.md"
        if isinstance(sol_data, dict):
            guide_rel = (sol_data.get("deployment") or {}).get("guide_file") or "guide.md"
        zh_rel = guide_rel[:-3] + "_zh.md" if guide_rel.endswith(".md") else guide_rel + "_zh.md"
        guide_files = [(guide_rel, "en"), (zh_rel, "zh")]
        any_guide = False
        for fname, lang in guide_files:
            gpath = sol_path / fname
            if not gpath.is_file():
                continue
            any_guide = True
            result = mp.parse_single_language_guide(
                gpath.read_text(encoding="utf-8"), lang
            )
            for perr in result.errors:
                errors.append(f"{fname}: {perr}")
        if not any_guide:
            errors.append("no guide.md (or guide_zh.md) found — cannot validate steps")

    # --- report --------------------------------------------------------------
    sol_id = sol_path.name
    if errors:
        print(f"✗ {sol_id} invalid ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"✓ {sol_id} valid")
    return 0
