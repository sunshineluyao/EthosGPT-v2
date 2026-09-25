#!/usr/bin/env python3
"""Rebuild the 64-country analysis from versioned, validated model outputs."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/gpt55_gpt56_64country"


def run(relative: str, *arguments: str) -> None:
    command = [sys.executable, str(ROOT / relative), *arguments]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    # Fix timestamps and timezone even when this script is called directly
    # rather than through the Makefile, so generated figure bytes are stable.
    os.environ.setdefault("SOURCE_DATE_EPOCH", "1788566400")
    os.environ.setdefault("TZ", "UTC")
    run("experiments/gpt55_gpt56_64country/score_wave1.py")
    run("experiments/gpt55_gpt56_64country/uncertainty_sensitivity.py")
    run("experiments/gpt55_gpt56_64country/protocol_sensitivity.py")
    run("experiments/gpt55_gpt56_64country/wording_sensitivity.py")
    run("experiments/gpt55_gpt56_64country/eight_region_sensitivity.py")
    run("experiments/gpt55_gpt56_64country/spatial_hac.py")
    run("experiments/gpt55_gpt56_64country/extended_analysis.py")
    run("scripts/make_wave1_assets.py")
    run("scripts/make_v070_assets.py")
    run("scripts/make_visual_story_v100.py")
    run("scripts/verify_results.py")
    run("scripts/audit_visual_assets.py")
    print("PASS: archived outputs -> statistics -> eight regions -> reproducible figures; no manuscript sources")

if __name__ == "__main__":
    main()
