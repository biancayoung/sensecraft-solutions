"""Tests for the offline ``validate`` command (zero engine dependency)."""

from __future__ import annotations

from pathlib import Path

from solutionctl.commands import validate

# Repo root: packages/solutionctl/tests/test_validate.py -> up 3 levels.
REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC_DIR = REPO_ROOT / "spec"
REAL_SOLUTION = REPO_ROOT / "solutions" / "recamera_heatmap_grafana"


def test_validate_real_solution_passes(capsys):
    """A real, valid solution validates with exit code 0."""
    rc = validate.run(str(REAL_SOLUTION), spec_dir=str(SPEC_DIR))
    assert rc == 0
    out = capsys.readouterr().out
    assert "valid" in out
    assert "recamera_heatmap_grafana" in out


def _write_min_solution(base: Path) -> None:
    """Write a minimal but valid-ish solution skeleton under ``base``."""
    base.mkdir(parents=True, exist_ok=True)
    (base / "solution.yaml").write_text(
        "version: 1\n"
        "id: broken_solution\n"
        "name: Broken Solution\n"
        "intro:\n"
        "  description_file: description.md\n"
        "deployment:\n"
        "  guide_file: guide.md\n",
        encoding="utf-8",
    )
    (base / "guide.md").write_text(
        "## Step 1: Do thing {#dothing type=web_dashboard required=true "
        "config=devices/d.yaml}\n\nHello\n",
        encoding="utf-8",
    )


def test_validate_missing_required_field_fails(tmp_path, capsys):
    """A solution.yaml missing required schema fields fails with exit 1."""
    base = tmp_path / "broken_required"
    base.mkdir()
    # Missing required 'id', 'intro', 'deployment'.
    (base / "solution.yaml").write_text("name: No Id Here\n", encoding="utf-8")
    (base / "guide.md").write_text(
        "## Step 1: X {#x type=web_dashboard required=true config=devices/x.yaml}\n\nhi\n",
        encoding="utf-8",
    )

    rc = validate.run(str(base), spec_dir=str(SPEC_DIR))
    assert rc == 1
    err = capsys.readouterr().err
    assert "invalid" in err
    assert "solution.yaml" in err


def test_validate_illegal_step_type_fails(tmp_path, capsys):
    """A guide.md with an unknown step type= fails with exit 1."""
    base = tmp_path / "broken_steptype"
    _write_min_solution(base)
    # Overwrite guide with an illegal step type.
    (base / "guide.md").write_text(
        "## Step 1: Bad {#bad type=totally_bogus required=true config=devices/x.yaml}\n\nhi\n",
        encoding="utf-8",
    )

    rc = validate.run(str(base), spec_dir=str(SPEC_DIR))
    assert rc == 1
    err = capsys.readouterr().err
    assert "guide.md" in err
    assert "totally_bogus" in err


def test_validate_bad_device_yaml_fails(tmp_path, capsys):
    """An invalid devices/*.yaml fails schema validation with exit 1."""
    base = tmp_path / "broken_device"
    _write_min_solution(base)
    devices = base / "devices"
    devices.mkdir()
    # Device YAML that is the wrong shape entirely (a list, not an object).
    (devices / "d.yaml").write_text("- not\n- a\n- device\n", encoding="utf-8")

    rc = validate.run(str(base), spec_dir=str(SPEC_DIR))
    assert rc == 1
    err = capsys.readouterr().err
    assert "devices/d.yaml" in err


def test_validate_bad_spec_dir(tmp_path, capsys):
    """An explicit --spec-dir without the schema reports a friendly error."""
    base = tmp_path / "sol"
    _write_min_solution(base)
    rc = validate.run(str(base), spec_dir=str(tmp_path))
    assert rc == 1
    err = capsys.readouterr().err
    assert "cannot locate contract files" in err


def test_validate_missing_solution_path(tmp_path, capsys):
    rc = validate.run(str(tmp_path / "does_not_exist"), spec_dir=str(SPEC_DIR))
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_find_spec_dir_autodiscovery():
    """Auto-discovery walks up from the solution path to find spec/."""
    found = validate._find_spec_dir(REAL_SOLUTION, None)
    assert found is not None
    assert (found / "solution.schema.json").is_file()


def test_no_provisioning_station_import():
    """Sanity: the validate module source must not import the engine."""
    src = Path(validate.__file__).read_text(encoding="utf-8")
    assert "import provisioning_station" not in src
    assert "from provisioning_station" not in src
