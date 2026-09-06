#!/usr/bin/env python3
"""Create compact, auditable protocol files from a validated collector run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collector-run", type=Path, required=True)
    args = parser.parse_args()
    run = args.collector_run.resolve()
    index_path = run / "prepared/gpt55_attempt0_index.jsonl"
    collection_manifest_path = run / "collection_manifest.json"
    rows = read_jsonl(index_path)
    if len(rows) != 1_920:
        raise ValueError(f"Expected 1,920 GPT-5.5 index rows, found {len(rows)}")

    questions: dict[str, dict] = {}
    for row in rows:
        question_id = row["question_id"]
        candidate = {
            "question_id": question_id,
            "domain_label": row["domain"],
            "full_prompt_example": row["prompt"],
            "prompt_template": row["prompt"].replace(row["country"], "{{COUNTRY}}"),
            "response_choices": row["valid_choices"],
            "example_country": row["country"],
            "example_prompt_sha256": row["prompt_sha256"],
        }
        if question_id not in questions:
            questions[question_id] = candidate
        else:
            prior = questions[question_id]
            if prior["prompt_template"] != candidate["prompt_template"] or prior["response_choices"] != candidate["response_choices"]:
                raise ValueError(f"Prompt or response-choice drift within {question_id}")

    roster = (
        pd.DataFrame(rows)[["country_code", "country", "cultural_region"]]
        .drop_duplicates()
        .sort_values(["cultural_region", "country"])
    )
    if len(roster) != 64:
        raise ValueError(f"Expected 64 countries, found {len(roster)}")

    payload = {
        "protocol_id": rows[0]["protocol_id"],
        "wave": rows[0]["wave"],
        "prompt_set_sha256": json.loads(collection_manifest_path.read_text())["prompt_sha256"],
        "question_order": ["Q48", "Q57", "Q106", "Q108", "Q121", "Q159"],
        "questions": [questions[key] for key in ["Q48", "Q57", "Q106", "Q108", "Q121", "Q159"]],
        "generation_count": 5,
        "response_contract": "Strict JSON schema; one probability for every official category; non-negative probabilities summing to one; no explanation.",
        "reasoning_effort": "low",
        "tools": [],
        "store": False,
    }
    inputs = HERE / "inputs"
    manifests = HERE / "manifests"
    inputs.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    protocol_path = inputs / "questionnaire_and_prompts.json"
    roster_path = inputs / "country_roster.csv"
    prompt_ledger_path = inputs / "prompt_ledger.csv"
    protocol_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    roster.to_csv(roster_path, index=False)
    prompt_ledger = (
        pd.DataFrame(rows)[["country_code", "country", "cultural_region", "question_id", "domain", "prompt", "prompt_sha256"]]
        .drop_duplicates(["country", "question_id"])
        .sort_values(["country_code", "question_id"])
    )
    if len(prompt_ledger) != 384:
        raise ValueError(f"Expected 384 unique country-question prompts, found {len(prompt_ledger)}")
    prompt_ledger.to_csv(prompt_ledger_path, index=False)
    source = {
        "collector_run_directory_name": run.name,
        "source_index": "prepared/gpt55_attempt0_index.jsonl",
        "source_index_sha256": file_sha256(index_path),
        "collection_manifest_sha256": file_sha256(collection_manifest_path),
        "derived_protocol_sha256": file_sha256(protocol_path),
        "derived_country_roster_sha256": file_sha256(roster_path),
        "derived_prompt_ledger_sha256": file_sha256(prompt_ledger_path),
        "note": "The compact files preserve every prompt, response choice, and country-question prompt hash. Generation-specific request hashes remain in the frozen score outputs.",
    }
    (manifests / "protocol_source.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    print(protocol_path)
    print(roster_path)
    print(prompt_ledger_path)


if __name__ == "__main__":
    main()
