#!/usr/bin/env python3
"""Verify and reproduce the declared dynamic mechanisms in an isolated copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "experiments/dynamic_growth"
REQUIRED = {
    "parameters.json", "dynamics.py", "culture.py", "run_experiments.py",
    "test_dynamics.py", "inputs/culture_distributions.csv",
    "results/rollout_rate_grid.csv",
}


def validate_manifest(study: Path) -> int:
    records = json.loads((study / "RELEASE_MANIFEST.json").read_text())
    names = [record["relative_path"] for record in records]
    if len(names) != len(set(names)) or not REQUIRED.issubset(names):
        raise ValueError("dynamic manifest has duplicate or missing required entries")
    for record in records:
        path = study / record["relative_path"]
        if not path.resolve().is_relative_to(study.resolve()):
            raise ValueError("dynamic manifest path leaves the study directory")
        if not path.is_file():
            raise ValueError(f"missing dynamic reference file: {record['relative_path']}")
        data = path.read_bytes()
        if len(data) != record["size"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"dynamic checksum mismatch: {record['relative_path']}")
    return len(records)


def compare_outputs(reference: Path, generated: Path) -> dict:
    expected = sorted(p.name for p in (reference / "results").glob("*.csv"))
    actual = sorted(p.name for p in (generated / "results").glob("*.csv"))
    if expected != actual:
        raise ValueError("dynamic result file set differs from the governed reference")
    maximum_difference = 0.0
    for name in expected:
        before = pd.read_csv(reference / "results" / name)
        after = pd.read_csv(generated / "results" / name)
        if list(before.columns) != list(after.columns) or before.shape != after.shape:
            raise ValueError(f"dynamic result schema mismatch: {name}")
        for column in before.columns:
            if pd.api.types.is_float_dtype(before[column]):
                np.testing.assert_allclose(after[column], before[column], rtol=1e-9,
                                           atol=1e-10, equal_nan=True,
                                           err_msg=f"dynamic result drift: {name}:{column}")
                differences = np.abs(after[column].to_numpy() - before[column].to_numpy())
                if np.isfinite(differences).any():
                    maximum_difference = max(maximum_difference, float(np.nanmax(differences)))
            else:
                pd.testing.assert_series_equal(after[column], before[column], check_names=True)
    old = json.loads((reference / "results/numerical_checks.json").read_text())
    new = json.loads((generated / "results/numerical_checks.json").read_text())
    if new["status"] != "passed" or new["config_sha256"] != old["config_sha256"]:
        raise ValueError("dynamic numerical check or configuration mismatch")
    for key in ["policy_menu_size", "audit_linked_scenarios", "culture_family_scenarios",
                "lag_rate_scenarios", "rollout_rate_scenarios", "no_fold_control_states"]:
        if new[key] != old[key]:
            raise ValueError(f"dynamic scenario coverage differs: {key}")
    for key, limit in {
        "max_probability_mass_error": 1e-12, "max_fold_residual": 1e-9,
        "max_fold_zero_eigenvalue": 1e-9, "max_independent_fold_displacement": 1e-9,
        "max_cultural_mass_error": 1e-10, "common_budget_max_error": 1e-12,
        "max_policy_metric_tolerance_difference": 1.1e-11,
        "max_cultural_metric_tolerance_difference": 1.1e-7,
        "closed_resource_benchmark_residual": 1e-12,
    }.items():
        if not np.isfinite(new[key]) or new[key] > limit:
            raise ValueError(f"dynamic numerical tolerance exceeded: {key}")
    for key in ["countries", "questions", "paired_model_cells", "generations_per_cell"]:
        if new["audit_reproduction"][key] != old["audit_reproduction"][key]:
            raise ValueError(f"dynamic measured-input coverage differs: {key}")
    for key in ["mean_TVD_delta", "ci_low", "ci_high"]:
        np.testing.assert_allclose(new["audit_reproduction"][key], old["audit_reproduction"][key],
                                   rtol=0, atol=1e-12)
    return {"status": "passed", "csv_files_compared": len(expected),
            "maximum_absolute_csv_difference": maximum_difference,
            "relative_tolerance": 1e-9, "absolute_tolerance": 1e-10,
            "config_sha256": new["config_sha256"],
            "audit_linked_scenarios": new["audit_linked_scenarios"],
            "culture_family_scenarios": new["culture_family_scenarios"],
            "lag_rate_scenarios": new["lag_rate_scenarios"],
            "rollout_rate_scenarios": new["rollout_rate_scenarios"]}


def run(work: Path, *arguments: str) -> None:
    env = dict(os.environ)
    env.setdefault("SOURCE_DATE_EPOCH", "1788566400")
    env.setdefault("TZ", "UTC")
    subprocess.run([sys.executable, *arguments], cwd=work, env=env, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify the frozen companion only")
    mode.add_argument("--compare-only", action="store_true", help="compare an already completed run")
    mode.add_argument("--figures-only", action="store_true", help="render released results in an isolated copy")
    parser.add_argument("--output-dir", type=Path, help="isolated output; default is a new build/dynamic-growth-* directory")
    args = parser.parse_args()
    count = validate_manifest(STUDY)
    if args.check:
        print(f"PASS dynamic integrity: {count} governed files")
        return
    if args.compare_only and args.output_dir is None:
        raise ValueError("--compare-only requires the completed run's --output-dir")
    work = (args.output_dir or ROOT / "build" / f"dynamic-growth-{uuid4().hex[:12]}").resolve()
    if work.is_relative_to(STUDY.resolve()) or STUDY.resolve().is_relative_to(work):
        raise ValueError("the reproduction directory must be separate from the released companion")
    if not args.compare_only:
        if work.exists():
            raise ValueError("output directory already exists; select a new --output-dir")
        shutil.copytree(STUDY, work, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if not args.figures_only:
            run(work, "run_experiments.py")
            run(work, "-m", "unittest", "test_dynamics", "-v")
        run(work, "make_figures.py")
        run(work, "build_explorer.py")
    report = compare_outputs(STUDY, work)
    (work / "reproduction_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS dynamic reproduction:", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
