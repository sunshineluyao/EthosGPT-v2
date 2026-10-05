# Structural innovation and transition model (R3)

This experiment connects frozen aggregate survey/model profiles to an explicit
advice rule, a Cobb–Douglas creative-destruction market, and a constrained
dynamic welfare planner. Country labels identify **conditional resource
scenarios**, not fitted national forecasts. Groups A/B are illustrative
adjustment populations. All parameters, units and comparison rules are defined
in [the rule guide](../../docs/structural_growth_guide.md).

The earlier `experiments/dynamic_growth` coordination system remains separate.
Its feedback state, quality step, clock, spending identity, and heuristic
advice rule must not be substituted for the equations in this experiment.

## Run offline

From the repository root, using the locked Python environment:

```bash
python experiments/ah_growth/verify_results.py
python experiments/ah_growth/verify_values.py --root experiments/ah_growth --output /tmp/ah-bellman-check.json
python experiments/ah_growth/reproduce.py --refresh-metrics
python experiments/ah_growth/publication_figures.py
```

`verify_results.py` checks input-rule algebra, resource constraints, exact
held-control state steps, outcome definitions, matched sensitivity meshes,
and adviser contrasts. `verify_values.py` independently streams every reference
state/action pair to check the saved discrete Bellman equation. It checks a
cached solution, not a fresh continuous-control proof.

`reproduce.py --refresh-metrics` works in an isolated temporary copy, rebuilds
market boundary-value paths for all three countries, and recomputes actual-state
held-action planner paths, the 27 matched sensitivity metrics, and the four
joint refinements using released value arrays. It compares named numerical
metrics with the frozen reference outputs. It does not call models or change
the released results. This can take several minutes. Without the flag it runs
the faster scientific-contract check.

`country_revision_compute.py` is the lower-level computation entry point and
writes results locally. It solves a Bellman system if its matching NPZ cache is
absent. For a fully fresh discrete solve, delete matching `policy-*.npz` caches
in an isolated experiment copy, including corresponding `node2_results` caches;
fine-grid solves need substantial memory. Reference values are shipped so that
numerical and plotting checks remain practical. The original `node2.py` and
`node2_diagnostics.py` contain historical development routines; their old
interpolated-control planner diagnostics are not the reviewed R3 trajectories.

## Evidence and comparison scope

- Inputs: aggregate `inputs/country_question_scores.csv`; no new participant data.
- Primary results: `country_revision_results/country-policy-comparisons.csv`,
  `country-paths.csv`, `three-country-upgrade-comparison.csv`.
- Sensitivities: `matched-sensitivity.csv` uses 101 state points per dimension,
  61 action points per dimension, and decision interval .125 throughout.
- Refinement: `country-refinement.csv` changes state grid, action grid and time
  interval together; it is not an isolated state-grid convergence experiment.
- Value caches: 24 distinct finest-mesh country/parameter arrays, plus coarse
  reference arrays. A small Bellman residual does not bound every path measure.
- Publication figures: live-text SVG and vector PDF at seven-inch width;
  `publication_figures.py` uses the released numerical tables.

The adviser-version contrast changes only the represented profile and its
implied aid/research tax or subsidy in the same physical economy and market.
Outcome direction differs from change in absolute deviation from human advice.
The planner is a separate normative institution under the same feasible labor
cap, not an adviser-version treatment or an equal-spending experiment.

The welfare objective uses the **instantaneous** worst-group penalty before
integration. Reported `Umax` takes the maximum **after** group time averaging.
Expected log-quality growth uses `log(1+q)`; expected quality in welfare uses `q`.
`G` is cumulative gain, `g_log=G/H` a rate. Steady normalized needs with positive
research can coexist with continuing quality growth.

The R&D/GDP anchors are dated 2023 resource observations: China 2.58% (revised
NBS denominator), Germany 3.1% (rounded Eurostat), Egypt 1.03% (WIPO GII 2025,
PDF p.8, indicator 2.3.2). Their one-moment conversion to research productivity
depends on assumed cost/production parameters. The model clock, innovation
step, group flows and normative weights are unestimated. Kenya's historical
undated benchmark is retained only in development tables.

Complete uncertainty propagation, empirical group identification, general
continuous-control optimality, and implementation of the whole planner path
remain research tasks. The original uncapped linear-utility planner is
unbounded for these reference parameters; the declared cap makes this extension
finite. Do not attribute the cap, aid, or needs mechanism to the original theory.
