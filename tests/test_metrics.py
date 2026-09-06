from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance

from ethosgpt.pipeline import normalize_text


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/gpt55_gpt56_64country"


def test_normalize_text_handles_curly_apostrophes():
    assert normalize_text("Don´t know") == "don't know"


def test_normalized_wasserstein_identity():
    assert wasserstein_distance([0, 0.5, 1], [0, 0.5, 1]) == 0


def test_scale_width_contract():
    values = (np.array([1, 5, 10]) - 1) / 9
    assert np.allclose(values, [0, 4 / 9, 1])


def test_frozen_output_roster_and_pairing():
    rows = []
    for name in ("gpt-5.5_scores.jsonl", "gpt-5.6-sol_scores.jsonl"):
        with (EXP / "outputs" / name).open() as handle:
            data = [json.loads(line) for line in handle if line.strip()]
        assert len(data) == 1_920
        assert len({row["country"] for row in data}) == 64
        rows.extend(data)
    paired = pd.DataFrame(rows).groupby(["country", "question_id", "generation"])["display_name"].nunique()
    assert len(paired) == 1_920
    assert paired.eq(2).all()


def test_new_figure_and_appendix_contract():
    design = (ROOT / "paper/figs/figS2_study_design.svg").read_text()
    results = (ROOT / "paper/figs/fig2_multiview_results.svg").read_text()
    cases_figure = (ROOT / "paper/figs/figS5_country_profiles.svg").read_text()
    prompts = (ROOT / "paper/appendices/generated_questionnaire_prompts.tex").read_text()
    assert "64 countries" in design
    assert "Paired model" in design and "5 responses per cell" in design
    assert "Three" in design and "Economic" in design
    assert "Country ΔTVD distribution" in results and "Joint simultaneous intervals" in results
    assert "Pre-interaction residual" in results and "India profile" in results

    # The two model profiles are numerically near-coincident.  GPT-5.6 must be
    # drawn first and the hollow, dashed GPT-5.5 trajectory last so neither is
    # silently hidden; coordinates themselves remain unjittered.
    source = (ROOT / "scripts/make_visual_story_v100.py").read_text()
    assert 'radar_draw_order = ["GPT-5.6 Sol", "GPT-5.5"]' in source
    assert 'markerfacecolor=markerface' in source
    assert "residual_limit: float = .20" in source
    assert 'residuals = values - human_profile' in source
    assert "baseline_angles = np.linspace(0, 2 * np.pi, 361)" in source
    assert '["−0.15", "0", "+0.15"]' in source
    assert "Domain dumbbell" not in results and "Aligned profiles" not in results
    assert all(label in results for label in ("lower", "near zero", "higher"))
    assert "98.82%" in results and "98.69%" in results
    assert "#eaf0ff" in results and "#667687" in results
    assert "Nimbus Roman" in results
    assert "Distrib." in results and "Responsib." in results
    assert all(label in cases_figure for label in (
        "Lower CRG: Greece", "Near-zero CRG: Indonesia", "Higher CRG: Argentina"
    ))
    cases = pd.read_csv(ROOT / "paper/figure_sources/data/country_radar_case_selection.csv")
    assert cases.set_index("selection_role").country.to_dict() == {
        "main": "India",
        "appendix_lower": "Greece",
        "appendix_near_zero": "Indonesia",
        "appendix_higher": "Argentina",
    }
    assert "model outcomes excluded from selection" in cases.iloc[0].selection_rule
    assert np.isclose(cases.crg_class_threshold.nunique(), 1)
    assert prompts.count(r"\begin{promptlisting}") == 6
