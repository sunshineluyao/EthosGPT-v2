#!/usr/bin/env python3
"""Create an editable, evidence-status-aware bridge and case figure.

Observed signed answers come from the archived country-item result CSV.
The right-hand contrasts apply the declared adviser and quality-ladder rule
from the declared simulation rule; they are not observed economic outcomes.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from make_fig1_ethos_gallery import (
    AMBER, BLUE, DIVIDER, INK, LIGHT, PALE_GREEN, PALE_WARM,
    SLATE, TEAL, WHITE, line, mark, rect, rows, text,
)

HERE = Path(__file__).resolve().parent
OUT = Path(__file__).resolve().parents[2] / "results" / "figures"
DATA = HERE / "data"


def country_values(country: str):
    selection = {r["question_id"]: r for r in rows(DATA / "signed_country_items.csv")
                 if r["country"] == country}
    order = ["Q48", "Q57", "Q106", "Q108", "Q121", "Q159"]
    assert sorted(selection) == sorted(order)
    human = {q: float(selection[q]["human_directed"]) for q in order}

    def outcomes(profile):
        innovation = .5 + .30 * (profile["Q48"] + profile["Q159"] - 1)
        assistance = .5 + .30 * (profile["Q106"] - profile["Q108"])
        cooperation = .5 + .30 * (profile["Q57"] + profile["Q121"] - 1)
        arrival = .05 + .20 * innovation + .10 * cooperation
        return 100 * 20 * arrival * math.log(1.04), 100 * arrival * (1-assistance)

    baseline = outcomes(human)
    result = {}
    for version in ("55", "56"):
        bias = {q: float(selection[q]["signed_bias_" + version]) for q in order}
        model = {q: human[q] + bias[q] for q in order}
        quality, exposure = outcomes(model)
        result[version] = {"bias": bias, "quality_pp": quality - baseline[0],
                           "unassisted_per_100": exposure - baseline[1]}
    return result


def signed(value: float) -> str:
    return f"{value:+.2f}".replace("-", "−")


def build():
    nigeria, kenya = country_values("Nigeria"), country_values("Kenya")
    assert abs(nigeria["56"]["quality_pp"] + 1.68533272) < .0001
    assert abs(kenya["56"]["unassisted_per_100"] - 1.2687189) < .0001
    region = {r["model"]: {
        "quality_pp": float(r["mean_delta_20step_log_quality_pp"]),
        "unassisted_per_100": float(r["mean_delta_unassisted_transitions_per_100"])
    } for r in rows(DATA / "creative_eight_region_simulation.csv")
        if r["scenario"] == "illustrative" and r["cultural_region"] == "African-Islamic"}
    assert abs(region["GPT-5.5"]["quality_pp"] + .8971423) < .0001

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500" viewBox="0 0 900 500">',
        '<title>Six cultural questions influence a hypothetical innovation chance and transition assistance, yielding distinct efficiency and equity-exposure channels</title>',
        f'<defs><marker id="assumed-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1 1L9 5 1 9" fill="none" stroke="{AMBER}" stroke-width="1.7"/></marker></defs>',
        rect(0, 0, 900, 500, WHITE, WHITE, r=0, sw=0),
        text(20, 32, "How represented values may shape innovation and its costs", 25, INK, "bold"),
        text(20, 57, "Observed score gaps below; dashed amber links and economic outcomes are illustrative.", 17, SLATE),
        rect(18, 77, 273, 165, WHITE, TEAL),
        rect(310, 77, 272, 165, PALE_WARM, AMBER, dash="7 5"),
        rect(601, 77, 281, 165, WHITE, BLUE),
        rect(18, 253, 425, 231, WHITE, TEAL),
        rect(458, 253, 424, 231, PALE_WARM, AMBER, dash="7 5"),
    ]
    # Ports and gutters keep connectors away from text.
    for yy in (149, 180, 219):
        p.append(line(293, yy, 326, yy, AMBER, 2, "4 3",
                      'marker-end="url(#assumed-arrow)"'))
    p += [
        line(563, 153, 617, 153, AMBER, 2, "4 3", 'marker-end="url(#assumed-arrow)"'),
        line(563, 179, 591, 179, AMBER, 2, "4 3"),
        line(591, 179, 591, 204, AMBER, 2, "4 3"),
        line(591, 204, 617, 204, AMBER, 2, "4 3",
             'marker-end="url(#assumed-arrow)"'),
        line(563, 225, 617, 226, AMBER, 2, "4 3",
             'marker-end="url(#assumed-arrow)"'),
        rect(328, 135, 235, 56, WHITE, AMBER, r=6, sw=1.2),
        rect(328, 198, 235, 34, WHITE, AMBER, r=6, sw=1.2),
        rect(618, 134, 246, 48, WHITE, BLUE, r=6, sw=1.2),
        rect(618, 192, 246, 48, WHITE, BLUE, r=6, sw=1.2),
        # Short incumbent / taller new method is an illustrative quality ladder.
        '<g id="replacement-old">',
        rect(524, 153, 13, 21, LIGHT, SLATE, r=1, sw=1),
        '</g><g id="replacement-new">',
        rect(546, 148, 13, 26, PALE_GREEN, TEAL, r=1, sw=1),
        '</g>',
        line(539, 159, 545, 159, INK, 1.1),
        text(35, 103, "Six value questions", 20, INK, "bold"),
        text(35, 125, "Survey or model description", 17, SLATE),
        text(35, 151, "Q48 agency + Q159 science", 18, INK),
        text(35, 183, "Q57 trust + Q121 immigration", 18, INK),
        text(35, 210, "Q106 equality −", 18, INK),
        text(35, 231, "Q108 individual provision", 18, INK),
        text(328, 103, "Assumed mechanism", 20, INK, "bold"),
        text(328, 125, "Not estimated decisions", 17, SLATE),
        '<g id="lambda-label">',
        text(341, 158, "λ · innovation arrival", 18, INK, "bold"),
        '</g>',
        text(341, 180, "chance of replacement", 17, SLATE),
        text(341, 222, "a · transition assistance", 18, INK, "bold"),
        text(618, 103, "Two outcome channels", 20, INK, "bold"),
        text(618, 125, "Same choices, different stakes", 17, SLATE),
        text(633, 156, "G · efficiency channel", 18, INK, "bold"),
        text(633, 175, "Higher = more quality gain", 17, SLATE),
        text(633, 213, "U · equity risk", 18, INK, "bold"),
        text(633, 232, "Higher = more exposure", 17, SLATE),
        text(35, 281, "Observed | Nigeria vs survey", 20, INK, "bold"),
        text(35, 301, "Signed score: left = less of that view", 17, SLATE),
        text(476, 281, "Conditional | G and U", 20, INK, "bold"),
        text(476, 301, "Model-guided minus survey-guided", 17, SLATE),
    ]

    names = [("Q48", "Agency"), ("Q57", "Trust"),
             ("Q106", "Income equality*"), ("Q108", "Individual provision"),
             ("Q121", "Immigration*"), ("Q159", "Science opportunity")]
    def signed_x(v): return 222 + (v+.25)/.55 * (420-222)
    p.append('<g id="nigeria-axis">')
    for tick in (-.2, 0, .2):
        x = signed_x(tick)
        p += [line(x, 310, x, 422, INK if tick == 0 else DIVIDER,
                   1.4 if tick == 0 else 1),
              text(x, 442, "0" if tick == 0 else f"{tick:+.1f}", 18, SLATE,
                   anchor="middle")]
    p.append('</g>')
    p.append('<g id="nigeria-paired-marks">')
    for k, (qid, label) in enumerate(names):
        y = 323 + 18.3*k
        v55, v56 = nigeria["55"]["bias"][qid], nigeria["56"]["bias"][qid]
        p += [text(35, y+4, label, 18, INK),
              line(signed_x(v55), y-3, signed_x(v56), y-3, BLUE, 1.5),
              mark(signed_x(v55), y-5, BLUE, "circle", 3.2, True),
              mark(signed_x(v56), y+1, INK, "circle", 3.6)]
    p.append('</g>')
    p += [mark(42, 464, BLUE, "circle", 3.3, True),
          text(53, 470, "GPT-5.5", 18, SLATE),
          mark(173, 464, INK, "circle", 3.6),
          text(186, 470, "GPT-5.6 Sol", 18, SLATE),
          text(321, 470, "* wording", 17, SLATE)]
    # G and U have different units: show their signed values side by side.
    p += [text(476, 331, "Place", 17, INK, "bold"),
          text(607, 331, "G ↑: more gain", 17, INK, "bold"),
          text(744, 331, "U ↑: more risk", 17, INK, "bold"),
          line(476, 340, 864, 340, DIVIDER, 1),
          line(596, 313, 596, 447, DIVIDER, 1),
          line(733, 313, 733, 447, DIVIDER, 1)]
    cases = [
        ("Nigeria", nigeria["55"], nigeria["56"]),
        ("Afr.–Islamic", region["GPT-5.5"], region["GPT-5.6 Sol"]),
        ("Kenya", kenya["55"], kenya["56"]),
    ]
    p.append('<g id="scenario-paired-rows">')
    for k, (label, first, second) in enumerate(cases):
        y = 366 + 37*k
        p += [text(476, y, label, 18, INK),
              text(607, y, signed(first["quality_pp"])+" → "+
                   signed(second["quality_pp"]), 18, "#9C5F0C"),
              text(744, y, signed(first["unassisted_per_100"])+" → "+
                   signed(second["unassisted_per_100"]), 18, "#9C5F0C")]
        if k < 2:
            p.append(line(476, y+12, 864, y+12, DIVIDER, .8))
    p.append('</g>')
    p += [text(476, 471, "5.5 → 5.6 Sol; G in pp, U in index units.", 17, SLATE),
          "</svg>"]

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "fig2_value_bridge.svg"
    path.write_text("".join(p), encoding="utf-8")
    provenance = {
        "figure": "fig2_value_bridge",
        "reader_task": "Trace six value questions through the declared lambda/a rule to efficiency G and equity-relevant exposure U.",
        "iconography_mode": "minimal-scientific",
        "topology": {
            "questions": "observed survey and archived model descriptions",
            "lambda": "assumed chance of innovation; appendix intermediates i and s are substituted in main Equation (1)",
            "a": "assumed assistance intensity, distinct from fixed Greek alpha in appendix",
            "G": "higher is greater expected 20-round log-quality gain, not observed GDP",
            "U": "higher is greater replacement exposure weighted by lack of assumed assistance, not improved fairness or observed unemployment"
        },
        "evidence_classes": {
            "bottom_left": "archived model minus survey derivative, Nigeria",
            "bottom_right": "deterministic scenario, model minus corresponding survey-guided baseline"
        },
        "inputs": [
            "assets/figure_sources/data/signed_country_items.csv",
            "assets/figure_sources/data/creative_eight_region_simulation.csv",
            "experiments/gpt55_gpt56_64country/simulate_creative_destruction.py"
        ],
        "values": {"Nigeria": nigeria, "Kenya": kenya, "African-Islamic": region},
        "palette": {"ink": INK, "surface": WHITE, "primary": BLUE,
                    "secondary": TEAL, "status_accent": AMBER,
                    "divider": DIVIDER},
        "semantic_graphics": [
            {"concept": "quality-ladder replacement", "visual_encoding": "short incumbent and taller new method with a replacement direction", "shape_ids": ["replacement-old", "replacement-new", "lambda-label"], "origin": "original vector", "evidence_implication": "illustrative quality increment only"},
            {"concept": "observed Nigeria score errors", "visual_encoding": "paired signed marks against a survey-zero axis", "shape_ids": ["nigeria-paired-marks", "nigeria-axis"], "origin": "archived signed-country-item CSV", "evidence_implication": "descriptive model-minus-survey gaps"},
            {"concept": "conditional efficiency and equity paths", "visual_encoding": "paired version values for each of three places under two different outcome units", "shape_ids": ["scenario-paired-rows", "lambda-label"], "origin": "declared simulation code and archived inputs", "evidence_implication": "hypothetical contrasts, not economic outcomes"}
        ],
        "composition_mechanism": "Three branches of six question scores converge into lambda or assistance a; lambda feeds G and U while a feeds U. Descriptive gaps and conditional outcomes remain in separate lower panels.",
        "grayscale_encoding": "Solid teal boundary and hollow/filled version marks identify descriptive data; dashed boundaries and dashed arrows identify assumptions, with text labels on all paths.",
        "cautions": [
            "Q106 and Q121 recorded prompts have conflicting labels",
            "Region name is descriptive, not causal",
            "G and U are conditional outputs, not measured growth, employment, or fairness"
        ]
    }
    (HERE / "fig2_value_bridge_provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(path)


if __name__ == "__main__": build()
