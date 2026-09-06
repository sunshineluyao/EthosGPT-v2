from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr, wasserstein_distance


SEED = 20260828
MODELS = {
    "Alpaca-7B": "alpaca_with_demographics.tsv",
    "Vicuna-7B-v1.5": "vicuna_with_demographics.tsv",
    "Mixtral-8x7B": "mixtral_with_demographics.tsv",
    "GPT-3.5-Turbo": "gpt-3.5_with_demographics.tsv",
}
DOMAINS = {
    "Market": {"Q107": -1, "Q108": 1},
    "Distribution": {"Q106": -1},
    "Trust": {"Q57": -1, "Q58": -1, "Q59": -1},
    "Inclusion": {"Q121": 1, "Q122": 1, "Q123": 1},
    "Science": {"Q158": 1, "Q159": 1, "Q160": -1},
    "Agency": {"Q48": 1, "Q199": -1, "Q200": -1, "Q201": -1},
}
QUESTION_DOMAIN = {q: d for d, items in DOMAINS.items() for q in items}
QUESTION_DIRECTION = {q: direction for items in DOMAINS.values() for q, direction in items.items()}

# Patterns operate only on the isolated target question, never on the persona text.
QUESTION_PATTERNS = [
    ("Q123", r"immigra\w*.*strengthen\w*.*cultural diversity"),
    ("Q122", r"immigra\w*.*fill\w*.*(?:job|vacanc)"),
    ("Q121", r"impact of immigrants?.*development"),
    ("Q158", r"(?:healthier.*easier|easier.*comfortable)"),
    ("Q159", r"opportunit\w*.*next generation"),
    ("Q160", r"depend too much on science|not enough on faith"),
    ("Q177", r"claim\w*.*government benefits"),
    ("Q178", r"(?:avoid\w*.*fare|fare evasion).*public transport|avoiding a fare"),
    ("Q235", r"(?:having )?a strong leader.*(?:parliament|election)"),
    ("Q236", r"(?:having )?experts.*(?:not government|make decisions)"),
    ("Q237", r"(?:having )?(?:the )?army rule"),
    ("Q113", r"state authorities.*(?:involved in )?corruption"),
    ("Q114", r"business executives.*(?:involved in )?corruption"),
    ("Q112", r"(?:views? on corruption|no corruption.*abundant corruption)"),
    ("Q107", r"(?:private|government|state) (?:business )?ownership|ownership of (?:business|industry)"),
    ("Q108", r"(?:government|people) should take more responsibility|responsibility.*(?:everyone|provide)"),
    ("Q106", r"incomes? should be.*equal|larger income differences"),
    ("Q57", r"most people can be trusted|need to be (?:very )?careful.*(?:dealing with )?people"),
    ("Q58", r"(?:how much (?:do )?(?:you )?trust|trust people).*family"),
    ("Q59", r"(?:how much (?:do )?(?:you )?trust|trust people).*neighbou?r"),
    ("Q131", r"how secure.*neighbou?r|secure do you feel.*neighbou?r"),
    ("Q132", r"robberies.*(?:occur|neighbou?r)|how frequently.*robberies"),
    ("Q133", r"alcohol.*(?:street|neighbou?r)"),
    ("Q165", r"do you believe in god"),
    ("Q166", r"(?:do you )?believe in life after death"),
    ("Q164", r"how important.*god.*(?:your )?life"),
    ("Q176", r"(?:trouble )?deciding.*moral rules|moral rules.*right"),
    ("Q199", r"how interested.*politics"),
    ("Q200", r"discuss political matters"),
    ("Q201", r"daily newspaper"),
    ("Q48", r"free choice and control"),
    ("Q46", r"(?:taking all things together.*happy|overall happiness|how happy are you)"),
    ("Q47", r"(?:state of health|rate your.*health)"),
    ("Q1", r"(?:how important is family|would you say family is|family is very important).*life"),
    ("Q2", r"(?:how important are friends|would you say friends is|friends is very important).*life"),
    ("Q3", r"(?:how important is leisure|would you say leisure time is|leisure time is very important).*life"),
]


@dataclass(frozen=True)
class Inputs:
    world_values_bench: Path
    hf_train: Path
    hf_test: Path
    ethosgpt: Path


def normalize_text(value: object) -> str:
    value = str(value).strip().lower().replace("’", "'").replace("´", "'")
    value = re.sub(r"\s+", " ", value)
    return re.sub(r"[^a-z0-9']+", " ", value).strip()


def extract_target_question(prompt: str) -> str | None:
    matches = list(re.finditer(r"(?i)following\s+question", prompt))
    if matches:
        target = prompt[matches[-1].end() :].strip()
        if re.fullmatch(r"[?!.:,;\s-]*", target):
            return None
        for _ in range(5):
            old = target
            target = re.sub(r"(?is)^\s*[?:.,;\-]*\s*(?:question\s*:)?\s*", "", target)
            target = re.sub(
                r"(?is)^\s*(?:from|based on|given|considering|in light of|for)\b[^:.\n]{0,160}[.:]\s*",
                "",
                target,
            )
            target = re.sub(r"(?is)^\s*(?:is )?posed(?: to (?:him|her|them))?\s*:\s*", "", target)
            if target == old:
                break
        return target.strip() or None
    matches = list(re.finditer(r"(?i)question\s*:", prompt))
    if matches:
        target = prompt[matches[-1].end() :].strip()
        return target if len(target) > 8 else None
    return None


def identify_question(target: str | None) -> str | None:
    if not target:
        return None
    text = target.lower().replace("’", "'").replace("´", "'")
    found = [qid for qid, pattern in QUESTION_PATTERNS if re.search(pattern, text, re.S)]
    return found[0] if len(found) == 1 else None


def answer_lookup(codebook: dict, qid: str) -> dict[str, int]:
    return {
        normalize_text(label): int(code)
        for code, label in codebook[qid]["choices"].items()
        if int(code) >= 0
    }


def map_answer(answer: object, target: str, qid: str, codebook: dict) -> float:
    text = normalize_text(answer)
    lookup = answer_lookup(codebook, qid)
    if text in lookup:
        value = lookup[text]
    elif re.fullmatch(r"\d+(?:\.0+)?", text):
        value = int(float(text))
    else:
        return np.nan
    # The public SFT derivative reverses the numeric endpoints of Q108.
    if qid == "Q108" and re.fullmatch(r"\d+(?:\.0+)?", text):
        if "1 means 'people should take more responsibility" in target.lower().replace("’", "'"):
            value = 11 - value
    valid = {int(k) for k in codebook[qid]["choices"] if int(k) >= 0}
    return float(value) if value in valid else np.nan


def country_crosswalk(ethosgpt: Path) -> pd.DataFrame:
    source = pd.read_csv(ethosgpt / "data" / "indices.csv")
    year_col = source["Year"].astype(str)
    codes = year_col.str.extract(r"^(\d+?)(?:19|20)\d{2}\s", expand=False).astype(int)
    return pd.DataFrame(
        {
            "country_code": codes,
            "country": source["Country"],
            "cultural_region": source["Cultural_Region"],
            "traditional_secular": source["Traditional_vs_Secular"],
            "survival_self_expression": source["Survival_vs_SelfExpression"],
        }
    ).drop_duplicates("country_code")


def load_human_matches(inputs: Inputs, out: Path) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    wvb = inputs.world_values_bench
    parts = []
    for path in [inputs.hf_train, inputs.hf_test]:
        frame = pd.read_parquet(path, columns=["id", "question", "answer"])
        parts.append(frame)
    human = pd.concat(parts, ignore_index=True)
    human["target_question"] = human["question"].map(extract_target_question)
    human["question_id"] = human["target_question"].map(identify_question)
    codebook = json.loads((wvb / "dataset_construction" / "codebook.json").read_text())
    metadata = json.loads((wvb / "dataset_construction" / "question_metadata.json").read_text())
    human = human[human["question_id"].notna()].copy()
    human["human_score"] = [
        map_answer(a, t, q, codebook)
        for a, t, q in zip(human["answer"], human["target_question"], human["question_id"])
    ]
    human = human[human["human_score"].notna()].copy()
    duplicate_audit = (
        human.groupby(["id", "question_id"])["human_score"]
        .agg(["size", "nunique"])
        .reset_index()
    )
    ambiguous = set(
        map(tuple, duplicate_audit.loc[duplicate_audit["nunique"] > 1, ["id", "question_id"]].to_numpy())
    )
    if ambiguous:
        keep = [
            (int(i), q) not in ambiguous
            for i, q in zip(human["id"], human["question_id"])
        ]
        human = human[keep]
    human = human.drop_duplicates(["id", "question_id"], keep="first")
    human["country_code"] = human["id"].astype(int) // 1_000_000
    human = human.merge(country_crosswalk(inputs.ethosgpt), on="country_code", how="left", validate="many_to_one")
    human = human[human["country"].notna()].copy()
    human["scale_min"] = human["question_id"].map(lambda q: metadata[q]["answer_scale_min"])
    human["scale_max"] = human["question_id"].map(lambda q: metadata[q]["answer_scale_max"])
    human["human_norm"] = (human["human_score"] - human["scale_min"]) / (
        human["scale_max"] - human["scale_min"]
    )
    human["domain"] = human["question_id"].map(QUESTION_DOMAIN)
    human["direction"] = human["question_id"].map(QUESTION_DIRECTION)
    human = human[human["domain"].notna()].copy()
    human["human_directed"] = np.where(
        human["direction"] > 0, human["human_norm"], 1 - human["human_norm"]
    )
    human["participant_id"] = human["id"].astype(int)
    audit = {
        "hf_rows": int(sum(len(x) for x in parts)),
        "exact_valid_human_country_item_rows": int(len(human)),
        "ambiguous_duplicate_pairs_excluded": int(len(ambiguous)),
        "countries": int(human["country"].nunique()),
        "selected_questions": sorted(human["question_id"].unique()),
        "hf_commits": {"dataset": "026d11792ba88decb0b1198116a57745a8132433"},
        "worldvaluesbench_commit": "635db7455e2c656978929210eba984bc09ddd659",
        "ethosgpt_commit": "d9d15ab588a8159f0913de5e656d8f9d76bef05a",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "matching_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return human, metadata, duplicate_audit


def load_models(inputs: Inputs, metadata: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    joined = []
    failures = []
    base = inputs.world_values_bench / "evaluation" / "model_outputs"
    for model, filename in MODELS.items():
        frame = pd.read_csv(base / filename, sep="\t").rename(
            columns={"PARTICIPANT_ID": "participant_id", "QUESTION_ID": "question_id", "SCORE": "model_score"}
        )
        frame = frame[frame["question_id"].isin(QUESTION_DOMAIN)].copy()
        frame["model"] = model
        frame["scale_min"] = frame["question_id"].map(lambda q: metadata[q]["answer_scale_min"])
        frame["scale_max"] = frame["question_id"].map(lambda q: metadata[q]["answer_scale_max"])
        valid = frame["model_score"].between(frame["scale_min"], frame["scale_max"], inclusive="both")
        failures.append(
            pd.DataFrame(
                {
                    "model": [model],
                    "missing_score": [int(frame["model_score"].isna().sum())],
                    "out_of_range_score": [int((frame["model_score"].notna() & ~valid).sum())],
                }
            )
        )
        frame = frame[valid].copy()
        frame["model_norm"] = (frame["model_score"] - frame["scale_min"]) / (
            frame["scale_max"] - frame["scale_min"]
        )
        frame["direction"] = frame["question_id"].map(QUESTION_DIRECTION)
        frame["domain"] = frame["question_id"].map(QUESTION_DOMAIN)
        frame["model_directed"] = np.where(
            frame["direction"] > 0, frame["model_norm"], 1 - frame["model_norm"]
        )
        frame["country_code"] = frame["participant_id"].astype(int) // 1_000_000
        frame = frame.merge(country_crosswalk(inputs.ethosgpt), on="country_code", how="left", validate="many_to_one")
        frame = frame[frame["country"].notna()].copy()
        joined.append(frame)
    return pd.concat(joined, ignore_index=True), pd.concat(failures, ignore_index=True)


def item_distributions(long: pd.DataFrame, value: str, who: str) -> pd.DataFrame:
    group = ["country", "country_code", "question_id"] + (["model"] if "model" in long.columns else [])
    dist = long.groupby(group + [value], dropna=False).size().rename("count").reset_index()
    dist["n"] = dist.groupby(group)["count"].transform("sum")
    dist["probability"] = dist["count"] / dist["n"]
    return dist.rename(columns={value: "score"}).assign(source=who)


def country_profiles(long: pd.DataFrame, value: str, model: bool = False) -> pd.DataFrame:
    group = ["country", "country_code", "cultural_region", "domain"]
    if model:
        group.insert(0, "model")
    prof = long.groupby(group, dropna=False)[value].agg(["mean", "count"]).reset_index()
    return prof.rename(columns={"mean": "score", "count": "n"})


def wide_profiles(profile: pd.DataFrame, model: str | None = None) -> pd.DataFrame:
    frame = profile if model is None else profile[profile["model"] == model]
    return frame.pivot_table(index="country", columns="domain", values="score", aggfunc="first")


def standardized_crg(human: pd.DataFrame, ai: pd.DataFrame) -> pd.DataFrame:
    h = wide_profiles(human)
    sigma = h.std(axis=0).replace(0, np.nan)
    rows = []
    for model in MODELS:
        a = wide_profiles(ai, model)
        common = h.index.intersection(a.index)
        for country in common:
            delta = (a.loc[country] - h.loc[country]) / sigma
            present = delta.dropna()
            if len(present) >= 4:
                rows.append(
                    {
                        "model": model,
                        "country": country,
                        "crg": float(np.sqrt(np.mean(np.square(present)))),
                        "domains": int(len(present)),
                    }
                )
    return pd.DataFrame(rows)


def geometry_metrics(human: pd.DataFrame, ai: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    h = wide_profiles(human)
    rows = []
    rng = np.random.default_rng(seed)
    for model in MODELS:
        a = wide_profiles(ai, model)
        common = h.dropna().index.intersection(a.dropna().index)
        hh, aa = h.loc[common].to_numpy(), a.loc[common].to_numpy()
        if len(common) < 4:
            continue
        hd, ad = pdist(hh), pdist(aa)
        vdr = float(ad.mean() / hd.mean()) if hd.mean() else np.nan
        csr = float(spearmanr(hd, ad).statistic)
        perm = []
        for _ in range(499):
            perm.append(spearmanr(hd, pdist(aa[rng.permutation(len(aa))])).statistic)
        p = (1 + sum(abs(x) >= abs(csr) for x in perm)) / (1 + len(perm))
        rows.append({"model": model, "countries": len(common), "vdr": vdr, "csr": csr, "csr_perm_p": p})
    return pd.DataFrame(rows)


def item_w1(human: pd.DataFrame, models: pd.DataFrame) -> pd.DataFrame:
    rows = []
    human_groups = {
        key: group["human_norm"].to_numpy()
        for key, group in human.groupby(["country", "question_id"])
    }
    for (model, country, question), g in models.groupby(["model", "country", "question_id"]):
        human_values = human_groups.get((country, question))
        if human_values is None or len(human_values) == 0:
            continue
        rows.append(
            {
                "model": model,
                "country": country,
                "question_id": question,
                "n_human": len(human_values),
                "n_model": len(g),
                "w1": float(wasserstein_distance(human_values, g["model_norm"])),
            }
        )
    return pd.DataFrame(rows)


def bootstrap_summary(crg: pd.DataFrame, geometry: pd.DataFrame, w1: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    for model in MODELS:
        values = crg.loc[crg["model"] == model, "crg"].dropna().to_numpy()
        boots = np.array([rng.choice(values, len(values), replace=True).mean() for _ in range(1000)])
        w1_median = w1.loc[w1["model"] == model, "w1"].median()
        geom = geometry[geometry["model"] == model].iloc[0]
        rows.append(
            {
                "model": model,
                "crg": values.mean(),
                "crg_ci_low": np.quantile(boots, 0.025),
                "crg_ci_high": np.quantile(boots, 0.975),
                "countries": len(values),
                "vdr": geom["vdr"],
                "csr": geom["csr"],
                "csr_perm_p": geom["csr_perm_p"],
                "median_item_w1": w1_median,
            }
        )
    return pd.DataFrame(rows)


def simulation(crg: pd.DataFrame, human_profiles: pd.DataFrame, ai_profiles: pd.DataFrame) -> pd.DataFrame:
    h = wide_profiles(human_profiles)
    rows = []
    weights = {
        "innovation": {"Science": 0.5, "Market": 0.3, "Agency": 0.2},
        "transition": {"Distribution": 0.5, "Trust": 0.3, "Inclusion": 0.2},
        "safeguard": {"Inclusion": 0.5, "Science": 0.3, "Distribution": 0.2},
    }
    def policy(v: pd.Series) -> np.ndarray:
        return np.array([sum(v.get(k, np.nan) * w for k, w in spec.items()) for spec in weights.values()])
    for model in MODELS:
        a = wide_profiles(ai_profiles, model)
        for _, record in crg[crg["model"] == model].iterrows():
            country = record["country"]
            if country not in h.index or country not in a.index:
                continue
            hp, ap = policy(h.loc[country]), policy(a.loc[country])
            if np.isnan(hp).any() or np.isnan(ap).any():
                continue
            base = 0.5 * float(np.square(ap - hp).sum())
            for sensitivity in [0.5, 1.0, 2.0]:
                rows.append(
                    {
                        "model": model,
                        "country": country,
                        "crg": record["crg"],
                        "sensitivity": sensitivity,
                        "policy_regret": sensitivity * base,
                        "evidence_status": "SIM",
                    }
                )
    return pd.DataFrame(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(inputs: Inputs, project: Path) -> None:
    processed = project / "data" / "processed"
    analysis = project / "data" / "analysis_ready"
    tables = project / "results" / "tables"
    logs = project / "results" / "logs"
    simulation_dir = project / "results" / "simulation"
    for path in [processed, analysis, tables, logs, simulation_dir, project / "manifests"]:
        path.mkdir(parents=True, exist_ok=True)
    human, metadata, duplicate_audit = load_human_matches(inputs, logs)
    models, failures = load_models(inputs, metadata)
    human_dist = item_distributions(human, "human_score", "OBS")
    ai_long = models[["country", "country_code", "question_id", "model", "model_score"]].copy()
    ai_dist = item_distributions(ai_long, "model_score", "MOD")
    human_profiles = country_profiles(human, "human_directed")
    ai_profiles = country_profiles(models, "model_directed", model=True)
    crg = standardized_crg(human_profiles, ai_profiles)
    geom = geometry_metrics(human_profiles, ai_profiles)
    w1 = item_w1(human, models)
    table = bootstrap_summary(crg, geom, w1)
    sim = simulation(crg, human_profiles, ai_profiles)
    country_metrics = crg.merge(geom, on="model", how="left").assign(language="English", mode="matched_persona_frozen")

    human_dist.to_parquet(processed / "human_item_distributions.parquet", index=False)
    human_profiles.to_parquet(processed / "human_country_profiles.parquet", index=False)
    ai_dist.to_parquet(processed / "ai_item_distributions.parquet", index=False)
    ai_profiles.to_parquet(processed / "ai_country_profiles.parquet", index=False)
    country_metrics.to_parquet(analysis / "country_model_language_metrics.parquet", index=False)
    sim.to_parquet(simulation_dir / "simulation_runs.parquet", index=False)
    human[["participant_id", "country_code", "country", "cultural_region", "question_id", "domain", "human_score", "human_norm", "human_directed"]].to_parquet(
        analysis / "matched_human_evidence.parquet", index=False
    )
    models[["participant_id", "country_code", "country", "cultural_region", "question_id", "domain", "model", "model_norm", "model_directed"]].to_parquet(
        analysis / "matched_model_evidence.parquet", index=False
    )
    table.to_csv(tables / "table1_results.csv", index=False)
    w1.to_csv(tables / "item_w1_results.csv", index=False)
    failures.to_csv(logs / "failed_calls.csv", index=False)
    pd.DataFrame(
        [{"model": m, "provider": "archived upstream output", "input_tokens": np.nan, "output_tokens": np.nan, "cost_usd": np.nan, "note": "Historical costs not reported by upstream."} for m in MODELS]
    ).to_csv(logs / "api_costs.csv", index=False)
    duplicate_audit.to_csv(logs / "duplicate_pair_audit.csv", index=False)

    # One tidy file drives all panels; panel-specific schemas are identified explicitly.
    panel_rows = []
    region_by_country = human_profiles.drop_duplicates("country").set_index("country")["cultural_region"]
    for _, r in human_profiles.iterrows():
        panel_rows.append({"panel": "A", "model": "Human", "country": r.country, "cultural_region": r.cultural_region, "domain": r.domain, "x": r.score, "y": np.nan, "value": r.score})
    for _, r in ai_profiles.iterrows():
        panel_rows.append({"panel": "B", "model": r.model, "country": r.country, "cultural_region": r.cultural_region, "domain": r.domain, "x": r.score, "y": np.nan, "value": r.score})
    for _, r in crg.iterrows():
        panel_rows.append({"panel": "C", "model": r.model, "country": r.country, "cultural_region": region_by_country.get(r.country, ""), "domain": "CRG", "x": r.crg, "y": np.nan, "value": r.crg})
    for _, r in geom.iterrows():
        panel_rows += [
            {"panel": "D", "model": r.model, "country": "", "cultural_region": "", "domain": "VDR", "x": r.vdr, "y": np.nan, "value": r.vdr},
            {"panel": "D", "model": r.model, "country": "", "cultural_region": "", "domain": "CSR", "x": r.csr, "y": np.nan, "value": r.csr},
        ]
    domain_compare = ai_profiles.merge(
        human_profiles[["country", "domain", "score"]].rename(columns={"score": "human_score"}),
        on=["country", "domain"],
        how="inner",
    )
    domain_compare["abs_error"] = (domain_compare["score"] - domain_compare["human_score"]).abs()
    domain_error = domain_compare.groupby(["model", "domain"])["abs_error"].mean().rename("value").reset_index()
    for _, r in domain_error.iterrows():
        panel_rows.append({"panel": "E", "model": r.model, "country": "", "cultural_region": "", "domain": r.domain, "x": r.value, "y": np.nan, "value": r.value})
    for _, r in sim[sim.sensitivity == 1.0].iterrows():
        panel_rows.append({"panel": "F", "model": r.model, "country": r.country, "cultural_region": region_by_country.get(r.country, ""), "domain": "regret", "x": r.crg, "y": r.policy_regret, "value": r.policy_regret})
    pd.DataFrame(panel_rows).to_csv(tables / "figure3_panel_data.csv", index=False)

    outputs = [p for p in project.rglob("*") if p.is_file() and ".git" not in p.parts]
    checksums = "\n".join(f"{sha256(p)}  {p.relative_to(project)}" for p in sorted(outputs)) + "\n"
    (project / "manifests" / "file_checksums.sha256").write_text(checksums)
    manifest = pd.DataFrame([
        {"artifact": "Table 1", "source": "results/tabs/table1_results.csv", "command": "make metrics", "status": "DER"},
        {"artifact": "Figure 3", "source": "results/tabs/figure3_panel_data.csv + results/tabs/figure3_landscape_coordinates.csv", "command": "make figures", "status": "OBS+MOD+DER+SIM"},
        {"artifact": "Human profiles", "source": "data/processed/human_country_profiles.parquet", "command": "make human", "status": "OBS"},
        {"artifact": "AI profiles", "source": "data/processed/ai_country_profiles.parquet", "command": "make ai-offline", "status": "MOD"},
    ])
    manifest.to_csv(project / "manifests" / "results_manifest.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-values-bench", type=Path, required=True)
    parser.add_argument("--hf-train", type=Path, required=True)
    parser.add_argument("--hf-test", type=Path, required=True)
    parser.add_argument("--ethosgpt", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build(Inputs(args.world_values_bench, args.hf_train, args.hf_test, args.ethosgpt), args.project)
