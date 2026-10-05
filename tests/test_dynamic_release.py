"""Corrupt or missing dynamic inputs and altered governed results must fail."""
import json
import shutil

import pytest

from scripts.reproduce_dynamics import STUDY, compare_outputs, validate_manifest


def test_corrupt_dynamic_input_is_rejected(tmp_path):
    copy = tmp_path / "companion"
    shutil.copytree(STUDY, copy)
    with (copy / "inputs/culture_distributions.csv").open("ab") as stream:
        stream.write(b"\ncorrupt")
    with pytest.raises(ValueError, match="checksum mismatch"):
        validate_manifest(copy)


def test_missing_dynamic_input_is_rejected(tmp_path):
    copy = tmp_path / "companion"
    shutil.copytree(STUDY, copy)
    (copy / "inputs/culture_distributions.csv").unlink()
    with pytest.raises(ValueError, match="missing dynamic reference file"):
        validate_manifest(copy)


def test_changed_scenario_coverage_is_rejected(tmp_path):
    copy = tmp_path / "companion"
    shutil.copytree(STUDY, copy)
    path = copy / "results/numerical_checks.json"
    checks = json.loads(path.read_text())
    checks["audit_linked_scenarios"] -= 1
    path.write_text(json.dumps(checks))
    with pytest.raises(ValueError, match="scenario coverage differs"):
        compare_outputs(STUDY, copy)
