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


def build():
    nigeria = country_values("Nigeria")
    kenya = country_values("Kenya")
    assert abs(nigeria["56"]["quality_pp"] + 1.68533) < .0001
    assert abs(kenya["56"]["quality_pp"] - .70047) < .0001
    region = {r["model"]: float(r["mean_delta_20step_log_quality_pp"])
              for r in rows(DATA / "creative_eight_region_simulation.csv")
              if r["scenario"] == "illustrative" and r["cultural_region"] == "African-Islamic"}
    assert abs(region["GPT-5.5"] + .8971423) < .0001
    assert abs(region["GPT-5.6 Sol"] + 1.0115883) < .0001

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500" viewBox="0 0 900 500">',
         '<title>Six survey positions, an assumed adviser, creative destruction, and contrasting Global South cases</title>',
         f'<defs><marker id="theory-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1 1L9 5 1 9" fill="none" stroke="{INK}" stroke-width="1.7"/></marker><marker id="assumed-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1 1L9 5 1 9" fill="none" stroke="{AMBER}" stroke-width="1.7"/></marker></defs>',
         rect(0, 0, 900, 500, WHITE, WHITE, r=0, sw=0),
         text(20, 33, 'From represented values to technological change', 25, INK, 'bold'),
         text(20, 57, 'Nigeria scores are measured; amber adviser links and outcomes are assumed.', 17, SLATE),
         rect(18, 73, 273, 164, WHITE, TEAL),
         rect(310, 73, 272, 164, PALE_WARM, AMBER, dash='7 5'),
         rect(601, 73, 281, 164, WHITE, BLUE),
         text(35, 102, 'Six-item value profile', 20, INK, 'bold'),
         text(35, 124, 'Question-specific views, 0–1', 16, SLATE),
         text(328, 102, 'Assumed adviser choices', 20, INK, 'bold'),
         text(328, 124, 'Not estimated from behavior', 16, SLATE),
         text(618, 102, 'Quality ladder', 20, INK, 'bold'),
         text(618, 123, 'Aghion–Howitt mechanism', 16, SLATE)]
    pairs = [
        ('Q48 agency + Q159 science', 'Innovation support (i)'),
        ('Q57 trust + Q121 immigration', 'Cooperation (s)'),
        ('Q106 equality − Q108 provision', 'Transition assistance (a)'),
    ]
    for i, (item, action) in enumerate(pairs):
        y = 151 + i * 30
        p += [text(35, y, item, 16, INK),
              line(293, y-5, 306, y-5, AMBER, 1.8, '4 3', 'marker-end="url(#assumed-arrow)"'),
              text(328, y, action, 18, INK)]
    p += [line(585, 176, 597, 176, AMBER, 1.8, '4 3', 'marker-end="url(#assumed-arrow)"'),
          rect(618, 140, 97, 43, LIGHT, SLATE, r=3, sw=1.3),
          rect(756, 130, 109, 53, PALE_GREEN, TEAL, r=3, sw=1.3),
          text(666, 167, 'Old method', 17, INK, anchor='middle'),
          text(810, 152, 'New method', 17, INK, anchor='middle'),
          text(810, 173, 'higher quality', 16, TEAL, anchor='middle'),
          line(721, 159, 748, 159, INK, 2, extra='marker-end="url(#theory-arrow)"'),
          text(618, 205, 'λ = .05 + .20i + .10s (arrival)', 16, SLATE),
          text(618, 226, 'G20 = 20λ ln1.04; U = 100λ(1−a)', 16, SLATE),
          rect(18, 253, 425, 231, WHITE, TEAL),
          rect(458, 253, 424, 231, PALE_WARM, AMBER, dash='7 5'),
          text(35, 281, 'Observed | Nigeria vs survey', 20, INK, 'bold'),
          text(35, 301, 'Signed score: left = less of the named view', 16, SLATE),
          text(476, 281, 'Conditional | 20-round quality', 20, INK, 'bold'),
          text(476, 301, 'Gap vs survey-guided rule, percentage points', 16, SLATE)]

    names = [('Q48','Agency'), ('Q57','Trust'), ('Q106','Income equality*'),
             ('Q108','Individual provision'), ('Q121','Immigration*'),
             ('Q159','Science opportunity')]
    lx, rx = 222, 420
    def signed_x(v): return lx + (v+.25)/.55*(rx-lx)
    for tick in (-.2, 0, .2):
        x = signed_x(tick)
        p += [line(x, 310, x, 422, INK if tick==0 else DIVIDER, 1.4 if tick==0 else 1),
              text(x, 442, '0' if tick==0 else f'{tick:+.1f}', 16, SLATE, anchor='middle')]
    for i,(qid,label) in enumerate(names):
        y = 323 + 18.3*i
        a, b = nigeria['55']['bias'][qid], nigeria['56']['bias'][qid]
        p += [text(35, y+4, label, 16, INK),
              line(signed_x(a), y-3, signed_x(b), y-3, BLUE, 1.5),
              mark(signed_x(a), y-5, BLUE, 'circle', 3.2, True),
              mark(signed_x(b), y+1, INK, 'circle', 3.6)]
    p += [mark(42, 464, BLUE, 'circle', 3.3, True),text(53, 470, 'GPT-5.5', 16, SLATE),
          mark(161, 464, INK, 'circle', 3.6),text(173, 470, 'GPT-5.6 Sol', 16, SLATE),
          text(306, 470, '* wording', 16, SLATE)]

    cases = [
        ('Nigeria', nigeria['55']['quality_pp'], nigeria['56']['quality_pp']),
        ('African–Islamic', region['GPT-5.5'], region['GPT-5.6 Sol']),
        ('Kenya', kenya['55']['quality_pp'], kenya['56']['quality_pp']),
    ]
    x0,x1,lo,hi=632,855,-2.1,.85
    def quality_x(v): return x0+(v-lo)/(hi-lo)*(x1-x0)
    for tick in (-2,-1,0,.5):
        x=quality_x(tick)
        p += [line(x, 311, x, 423, INK if tick==0 else DIVIDER, 1.4 if tick==0 else 1),
              text(x, 442, f'{tick:+g}' if tick>.0 else str(tick), 16, SLATE, anchor='middle')]
    for i,(label,a,b) in enumerate(cases):
        y=334+i*39
        p += [text(476, y+4, label, 17, INK),
              line(quality_x(a), y-3, quality_x(b), y-3, AMBER, 2),
              mark(quality_x(a), y-5, AMBER, 'circle', 4.2, True),
              mark(quality_x(b), y+1, AMBER, 'circle', 4.5)]
    p += [mark(483, 464, AMBER, 'circle', 4.2, True),text(495, 470, 'GPT-5.5', 16, SLATE),
          mark(601, 464, AMBER, 'circle', 4.5),text(614, 470, 'GPT-5.6 Sol', 16, SLATE),
          text(748, 470, 'assumed', 16, SLATE),
          '</svg>']
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'fig2_value_bridge.svg'
    path.write_text(''.join(p), encoding='utf-8')
    provenance = {
        'figure':'fig2_value_bridge',
        'reader_task':'Show how a six-item profile enters a declared adviser rule, then how simulated effects differ within a descriptive region.',
        'topology':{'six items':'observed question-specific responses','adviser links':'assumed, not behavioral estimates','quality ladder':'Aghion–Howitt-inspired mechanism, not their complete equilibrium model'},
        'evidence_classes':{'bottom_left':'archived model minus unweighted survey derivative, Nigeria','bottom_right':'deterministic assumed scenario, each model minus survey-guided baseline'},
        'inputs':['assets/figure_sources/data/signed_country_items.csv','assets/figure_sources/data/creative_eight_region_simulation.csv','experiments/gpt55_gpt56_64country/simulate_creative_destruction.py (declared coefficients)'],
        'values':{'Nigeria':nigeria,'Kenya':kenya,'African-Islamic_quality_pp':region},
        'palette':{'ink':INK,'observed':TEAL,'model_pair':BLUE,'assumed':AMBER,'surface':[WHITE,PALE_WARM]},
        'cautions':['Q106 and Q121 recorded prompts have label conflicts','The cultural-region label is descriptive, not an identity or causal variable','The scenario does not observe growth, welfare, or emissions'],
    }
    (HERE / 'fig2_value_bridge_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(path)

if __name__ == '__main__': build()
