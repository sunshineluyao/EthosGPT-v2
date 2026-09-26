#!/usr/bin/env python3
"""Fast, offline integrity check for the archived EthosGPT release.

This does not rerun the bootstrap or spatial analyses. Use make reproduce-offline
and make release-contract for the full reference comparison.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate(root: Path) -> dict[str, object]:
    exp = root / "experiments/gpt55_gpt56_64country"
    manifest = json.loads((exp / "manifests/analysis_manifest.json").read_text(encoding="utf-8"))
    expected = {
        "GPT-5.5": ("gpt-5.5_scores.jsonl", 1920),
        "GPT-5.6 Sol": ("gpt-5.6-sol_scores.jsonl", 1920),
    }
    seen: set[tuple[str, str, int]] = set()
    for model, (name, count) in expected.items():
        path = exp / "outputs" / name
        actual = sha256(path)
        if actual != manifest["frozen_output_sha256"][model]:
            raise ValueError(f"frozen output checksum mismatch: {name}")
        with path.open(encoding="utf-8") as stream:
            records = [json.loads(line) for line in stream if line.strip()]
        if len(records) != count:
            raise ValueError(f"unexpected record count: {name}")
        for record in records:
            if record.get("status") != "valid":
                raise ValueError(f"nonvalid archived record: {name}")
            seen.add((str(record["country"]), str(record["question_id"]), int(record["generation"])))
    if len(seen) != 64 * 6 * 5:
        raise ValueError("country-question-generation coverage is incomplete")

    index = json.loads((root / "manifests/result_replication_index.json").read_text(encoding="utf-8"))
    for result in index["results"]:
        for key in ("query_code", "queried_data", "process_code", "processed_data", "analysis_code", "result_outputs"):
            for item in result[key]:
                if item.startswith("NOT_"):
                    continue
                if not (root / item).is_file():
                    raise ValueError(f"result {result['result_id']} has missing {key}: {item}")

    comparisons = rows(exp / "results/metric_comparisons.csv")
    tvd = next(r for r in comparisons if r["metric"] == "TVD")
    if abs(float(tvd["estimate"]) + .008046) > 5e-7:
        raise ValueError("global TVD reference drift")
    signed = rows(root / "results/signed_directions/signed_global_items.csv")
    if {r["question_id"] for r in signed} != {"Q48", "Q57", "Q106", "Q108", "Q121", "Q159"}:
        raise ValueError("six-item signed result set is incomplete")
    creative = rows(root / "results/creative_destruction/country_simulation.csv")
    if len(creative) != 64 * 2 * 5:
        raise ValueError("country scenario grid is incomplete")
    if any(p.suffix.lower() in {".tex", ".sty", ".bib"} or p.name == "latexmkrc"
           for p in root.rglob("*") if p.is_file()):
        raise ValueError("manuscript source found in code release")
    if (root / "paper").exists():
        raise ValueError("paper directory found in code release")
    return {
        "models": list(expected),
        "validated_model_records": sum(v[1] for v in expected.values()),
        "country_question_generation_cells": len(seen),
        "result_index_entries": len(index["results"]),
        "global_delta_tvd": float(tvd["estimate"]),
        "country_scenario_rows": len(creative),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print("PASS release smoke:", json.dumps(validate(args.root.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
