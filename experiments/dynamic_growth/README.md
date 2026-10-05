# Cultural representation, innovation, and adjustment over time

This companion study asks when an adviser that misreads values selects an innovation path that the actual system cannot sustain, and when assistance sustains progress within the same resources. It extends the archived six-question representation comparison with explicit dynamic mechanisms.

The survey and model distributions are measured inputs. The economic response, adjustment groups, cultural-change laws, and policy criteria are specified research assumptions. Country names identify sources of representation-error vectors evaluated in one common hypothetical economy. The results do not forecast countries' GDP, employment, or income inequality.

## Reproduce the study

From the repository root, use `make reproduce-dynamics` for a verified,
isolated run. `make mechanisms` runs the 13 mechanism tests, and
`make dynamic-figures` redraws the figures in a separate build directory.
The root runner compares 24 generated CSVs with the governed references and
preserves the released results. The [model guide](MODEL_GUIDE.md) explains the
equations, group meanings, policy rule, and outcome units; the
[dictionary](../../docs/dynamic_dictionary.md) defines the interdisciplinary terms.

The direct commands below are useful within a copied companion directory.

Use Python 3.12 and the versions in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
python run_experiments.py
python -m unittest test_dynamics -v
python make_figures.py
```

The full experiment run takes about three minutes on the execution host. Figures take several seconds. No provider calls, credentials, participant records, or Julia packages are needed. The six distributions are supplied as portable aggregate CSVs. Run in a copied directory to preserve the released `results/`; the runner writes that directory explicitly and does not alter any earlier experiment archive.

Run `python build_explorer.py` to regenerate the companion after changing results. Optional `node test_explorer.js` checks its numeric controls and script with a DOM fixture; it requires Node.js. The released explorer has not been browser-render tested because the execution host has no browser binary.

Open `explore.html` locally for an offline interactive companion. It reads embedded, precomputed scenarios and does not simulate new evidence or contact a server. The controls distinguish representation error, launch intensity, rollout speed, and information delay.

## What is added

| Scientific question | Experiment and evidence | Main finding and scope |
|---|---|---|
| Do new calculations preserve the measured comparison? | All 768 cell-level TVD/W1 comparisons and the primary 20,000-draw paired-country TVD interval | Maximum cell discrepancy 3.89e-16; original empirical archive unchanged. |
| Can misperception change a transition's course? | Shared actual three-state system; scalar and independent full-state fold checks; pseudo-arclength continuation | Illustrative optimistic advice loses adoption in the reinforcing system; the restoring-feedback control has a unique equilibrium and smooth outcomes. |
| Does distance determine consequence? | Three equal-TVD redistributions, plus 3,072 archived-profile/response combinations | Error direction, response strength, curvature, and item selection matter; zero strength reproduces the reference. |
| Does assistance widen viable rollout? | 35 rate/allocation choices; identical opportunities, initial states, and exact spending | A 2.5% diversion admits three of seven tested rates; zero and larger diversions admit none under the declared three criteria. This is a finite-grid, nonmonotonic result. |
| What if values change? | Five full-marginal cultural families, three response shapes, three policies; 45 scenarios | Drift, burden feedback, interaction, and memory/shocks change paths while preserving every probability simplex. |
| Does outdated advice matter? | 35 cultural-rate/update-lag comparisons | With lag six, fast change stalls adoption while slow change remains high. This combines changing culture with lagged policy response. |
| Must innovation have a sharp threshold? | Restoring-feedback control and closed-resource capital benchmark | Neither imposes a coordination fold; the capital ratio has one attracting positive equilibrium. |
| How do different transition mechanisms differ? | Separate aggregate phase portrait, pure rate-tipping equation, and analytic cusp normal form | Teaching examples are distinct from the economic experiment; no economic cusp or learned early-warning model is claimed. |

## Files and units

- `parameters.json`: complete coefficients, initial states, response functions, timing grids, criteria, and bootstrap settings.
- `dynamics.py`: quality replacement, group exposure, policy rule, stability, fold equations, and continuation.
- `culture.py`: all 47 category slots and five mass-preserving cultural-change families.
- `run_experiments.py`: measured-input reproduction and all dynamic comparisons.
- `test_dynamics.py`: 13 physical, algebraic, resource, and counterexample tests.
- `inputs/`: aggregate distributions, question dictionary, and frozen representation summaries.
- `results/`: complete scenario CSVs and numerical verification JSON.
- `sample_reproduction/`: unchanged supplied generator and model definitions, with instructions for regenerating all eight sample outputs.
- `sample_results/`: independently reproduced companion teaching samples; their aggregate phase model is distinct from the two-group system.
- `figures/`: editable SVG, publication PDF, and PNG exports, with input checksums and semantic provenance in `figure_manifest.json`.
- `INPUT_PROVENANCE.json`: input source versions and hashes, separate from assumed parameters.
- `SOURCES.md`: detailed primary sources and their roles.

Time is normalized adjustment time, not years. `growth` is mean log-quality growth per time; figure values multiply it by 100 and label log-quality points. `worst_burden` is the larger group's time-average unresolved-adjustment share. `adoption_final` is a share. Assistance consumes the same budget that supports launches. The capital benchmark closes consumption, policy, and investment resources but does not solve firms' research incentives.

## Interpretation and verification

The policy rule uses 94% of the estimated upper fold intensity and exhausts the budget. A belief changes the selected policy, not the actual attainable set. The finite-menu optimum is not a continuous global optimum. The criteria `growth >= 0.10`, `worst_burden <= 0.50`, and `adoption_final >= 0.50` are declared normative research objectives.

`results/numerical_checks.json` records independent fold checks, tolerance comparisons, mass conservation, budget equality, scenario counts, versions, runtime, and configuration hash. The stronger solver tolerance changes policy metrics by less than 1.1e-11 and cultural metrics by less than 1.1e-7. Low exposure accompanied by stalled adoption remains visible. Null, adverse, and response-dependent results are retained.

The six cross-sectional marginals cannot identify cultural evolution, institutions' response functions, or economic coefficients. Community-validated longitudinal measurement and decision experiments would estimate those links. Robust control, learned early warning, environmental outcomes, distributional welfare, and a full incentive-based endogenous-growth model remain research directions.
