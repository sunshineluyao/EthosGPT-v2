# Sample models, parameters, and figure provenance

All outputs in this package are **computed, uncalibrated mechanism illustrations**. Time, innovation intensity, cultural projection, and coordination are dimensionless. No survey observations or country economic data generate these figures. There are three distinct mathematical models; they are not one estimated economy.

## Model A: two-group transition ODE

States: coordination `z` (real valued), transition exposure `u_A,u_B` (shares), and cumulative mean log quality `q`. Define `x = sigmoid(2z)` and realized innovation hazard `lambda = nu*x`.

```
z'   = z - z^3 + b0 + c + beta*a - alpha*nu - chi*(u_A+u_B)/2
u_g' = d_g*nu*x*(1-u_g) - (r0_g+r1_g*a)*u_g
q'   = log(gamma)*nu*x
```

`a` is adjustment assistance. Innovation launch intensity `nu` costs `nu/capacity` resource units. Budget: `a + nu/capacity <= 1`. `c` is a **scalar projection used only to illustrate a cultural support channel**, not the planned generalized full distribution model. Changing an adviser's estimate of `c` does not change actual `c` in evaluation.

| Parameter | Value | Interpretation |
|---|---:|---|
| b0 | 0.70 | Baseline coordination tilt |
| beta | 0.45 | Assistance contribution to coordination |
| alpha | 0.90 | Launch pressure contribution |
| chi | 0.35 | Exposure feedback |
| d_A,d_B | 0.75,0.38 | Exposure entry multipliers |
| r0_A,r0_B | 0.12,0.32 | Baseline recovery rates |
| r1_A,r1_B | 1.20,1.00 | Aid contribution to recovery |
| gamma | 1.12 | Quality increment multiplier |
| capacity | 2.40 | Innovation intensity per resource share |
| actual c | 0.00 | Common evaluation culture |
| illustrative estimation bias | +0.18 | Adviser's assumed c; not TVD or measured API error |
| initial state | z=1.25; u_A=u_B=0.08; q=0 | Common initial state |
| horizon | 60 | Normalized time, not years |

These illustrative scales intentionally exhibit a fold. This is not evidence that an empirical economy has a fold. Far-from-critical and no-fold alternatives are required in the planned study.

For equilibria in `(z,u_A,u_B)`, use `u_g* = d_g*nu*x/(d_g*nu*x+r0_g+r1_g*a)`. Solve `F(z,nu,a,c)=0` after substituting these values. A high-branch fold solves `F=0` and total derivative `dF/dz=0`; stability is classified with the full **three-state Jacobian**, not just the scalar derivative. `q` is a growing accumulator and is excluded from the equilibrium subsystem.

The three illustrative policies exhaust exactly the same budget:

- Benchmark guidance chooses `nu = 0.94*nu_fold(a,0)` subject to `nu=2.4*(1-a)`.
- Biased guidance uses `nu = 0.94*nu_fold(a,0.18)` subject to the same budget.
- Adjusted policy sets `a=0.56`, `nu=2.4*(1-0.56)`. This is a hand-selected feasible illustration, not the computed optimal policy.

All realized paths use actual `c=0`. The perceived outcome in the Pareto figure uses `c=0.18` for the same selected policy, and is marked as a belief. Assistance and innovation are traded within the resource budget; no aid is free.

## Model A-aggregate: a separate phase-plane closure

The phase-plane sample is an exact **two-state aggregate model**, not a projection of all trajectories of Model A:

```
z' = z - z^3 + b0 + beta*a - alpha*nu - chi*u
u' = d*nu*sigmoid(2z)*(1-u) - r*u
```

`nu=1.10`, `a=0.30`, `d=0.565`, `r=0.22+1.1*a`, other coefficients as above. A vectorized RK4 integration classifies high/low basins at horizon 35. The saddle's stable eigenvector is followed backward until it reaches the plot boundary. Nullclines are contours where each derivative vanishes. Basin classification is numerical and finite-horizon.

## Model B: canonical rate-induced tipping

```
y' = -(y-l(t))^3 + (y-l(t))
l(t) = 1.5 * (tanh(rate*t)+tanh(40*rate)) / (2*tanh(40*rate))
```

Integration interval `[-40,40]`, initial `y=1`; rates `0.10` and `3.0`. Both use the same forcing function family and exactly the same initial/final forcing 0 and 1.5 on the finite interval. At every frozen forcing value, the equilibria `l±1` are stable and `l` is unstable. Stable branches never disappear. Slow forcing approaches the final high state `2.5`; fast forcing approaches the final low state `0.5`. This is a mathematical rate-tipping sample, not a calibrated economy or a claim about culture rates.

## Model C: cusp normal form

```
y' = alpha*y - y^3 + beta
beta = y^3 - alpha*y          (equilibrium sheet)
eigenvalue = alpha - 3*y^2
fold: y = ±sqrt(alpha/3), alpha>=0
cusp: alpha=beta=y=0
```

Surface domains: `alpha∈[-0.5,1.7]`, `y∈[-1.4,1.4]`. Stable/unstable sheets are determined analytically by the sign of the eigenvalue. This figure illustrates a possible visual treatment; it is not an identified economic singularity.

## Metric dictionary

| Name / data field | Calculation | Units / direction |
|---|---|---|
| `growth` | `(q(T)-q(0))/T` | Mean log-quality growth per normalized time; higher |
| `mean_burden` | Average of the two time-average exposure shares | Share; lower, conditional on adequate growth |
| `worst_burden` | Maximum of two group time-average exposures | Share; lower, conditional on adequate growth |
| `burden_gap` | Difference of group time-average exposures | Share; lower |
| `peak_worst` | Maximum instantaneous exposure across groups and time | Share; lower |
| `adoption_final` | `sigmoid(2*z(T))` | Share; not automatically welfare |
| `budget_used` | `a+nu/2.4` | Resource budget fraction |
| fold boundary | Critical `nu` where the high stable branch meets a saddle | Launch intensity; not forcing-path speed |
| realized fold hazard | `nu_fold*sigmoid(2*z_fold)` | Innovation hazard at that equilibrium |

Mean/worst exposure can decrease because technology adoption stalls. A low burden alone is not evidence of desirable social outcomes. No wage process is included; **Gini, income shares, GDP, welfare and unemployment are not reported**. No confidence intervals are invented.

## Data-to-figure mapping

| Figure | Model | Source data | Visual encoding |
|---|---|---|---|
| 01_boundary | A | data/boundary.csv | Aid x; launch intensity y; true/perceived fold; budget capacity; existence region |
| 02_bifurcation | A | data/bifurcation.csv | nu x; z y; line style encodes Jacobian stability; diamonds mark folds |
| 03_phase_basins | A-aggregate | data/phase_basins.csv + equations | Initial z,u; basin fill; derivative flow; nullclines; saddle stable manifold |
| 04_policy_trajectories | A | data/policy_trajectories.csv | Time x; adoption and group exposure in two panels; policies by colour, groups by line style |
| 05_efficiency_fairness | A | data/pareto_grid.csv, data/policy_metrics.json | Worst-group burden x; growth y; finite-grid actual envelope; selected/estimated outcomes |
| 06_rate_tipping | B | data/rate_tipping.csv | Time x; forcing and state; rates by colour; instantaneous high branch dotted |
| 07_cusp_surface | C | data/cusp_surface.csv | Two normal-form parameters and equilibrium; stability by sheet colour; gold fold curves |
| 00_sample_atlas | A, A-aggregate, B, C | Six of the above PNG files | Contact sheet, retaining labels/captions |

Finite-grid Pareto envelope uses 817 feasible policies and 60-unit paths. It is not a globally certified optimum. The three highlighted choices use identical actual budget expenditure, while the background feasible grid permits expenditure below the ceiling. They are evaluated from identical initial conditions. All advisers share the actual attainable set.

## Numerical and visual checks

`NUMERICAL_CHECKS.json` is written by an actual execution, not manually populated. It checks equilibrium/fold residuals, the full Jacobian's near-zero eigenvalue at the fold, ODE tolerance convergence, exposure bounds, common budgets, and a separate Markov–replicator simplex module. Rate-tipping final attractors are checked explicitly. No empirical or causal validation is implied.

`RUN_ENVIRONMENT.json` records tested Python and library versions; `requirements.txt` pins those versions. Figures use editable SVG text and vector PDF marks (apart from ordinary preview PNG). The atlas is a raster contact sheet; individual SVG/PDF files are the editable outputs.
