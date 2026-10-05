# Structural innovation, transition, and comparison rules

English explanation of the integrated R3 model and comparison rules, checked against the implementation on 5 October 2026. The revised manuscript supplies the main argument, full appendix definitions, a 22-term structural dictionary, and complete numerical coordinate tables. All model and numerical assumptions remain declared.

## The question and the intellectual foundation

Better prediction of a society's questionnaire answers need not produce advice closer to its reference choices. An institution responds to particular directions of error, and research and assistance have different costs and benefits. The experiment traces that link while keeping measured representation errors separate from assumed decision rules and simulated economic consequences.

The [Aghion–Howitt growth model](https://dash.harvard.edu/entities/publication/73120378-cb4d-6bd4-e053-0100007fdf3b) explains how research generates better technologies and replaces incumbent innovations and their profits. The [2025 economics prize](https://www.nobelprize.org/prizes/economic-sciences/2025/summary/) recognized that growth theory jointly with Mokyr's work on conditions supporting technological progress. The project adds assistance, temporary adjustment needs and an explicitly chosen welfare objective. Those additions are assumptions to test, not conclusions inherited from the prize-winning work.

## 1. How a profile becomes fixed advice

Let `x` contain directed scores in `[0,1]` for Q48, Q57, Q106, Q108, Q121 and Q159. A directed score is the mean coded response position; it is not the entire answer distribution or an individual's preferences. Define

$$
\begin{aligned}
i(x)&=i_0+b_i(x_{48}+x_{159}-1),\\
a(x)&=a_0+b_a(x_{106}-x_{108}),\\
s(x)&=s_0+b_s(x_{57}+x_{121}-1),\\
p_6(x)&=p_0+\alpha i(x)+\beta s(x).
\end{aligned}
$$

`i` is an innovation-support signal; `a` is assistance intensity; `s` is a cooperation-support signal. The assumed signs express how the hypothetical institution responds. They are not estimated welfare weights. Parameter ranges must keep the three signals and per-round probability valid. The same mapping is applied to human-reference, GPT-5.5 and GPT-5.6 profiles.

For `T` rounds of duration `delta`, an economic innovation multiplies quality by `gamma = 1+q`. The static measures are

$$G_T=T p_6\log(1+q),\qquad U_6=100p_6(1-a).$$

`G_T` is expected cumulative log-quality gain. `U_6` is an index of replacement pressure weighted by a lack of assumed help, per 100 activities per round. It is not a measured count of unemployed or unassisted people.

**Intuitive example.** If an innovation has a 20% probability per round and increases quality by 8%, ten rounds give expected log-quality gain `10 × 0.20 × log(1.08) ≈ 0.15392`. Assistance `a = 0.50` gives a pressure index `100 × 0.20 × 0.50 = 10`. Increasing help to `0.60` reduces that index to eight at the same arrival probability. This arithmetic illustrates the declared rule, not an estimated policy effect.

Implementation: `model.py: RuleParameters, section6`. R3's numerical rule uses the historical signal loadings with `q = 0.08`, `T = 20`, `delta = 5`; the older main-text example uses `q = 0.04`, `delta = 1`. Keep these as named scenarios rather than universal constants.

## 2. The bridge to continuous research and innovation

Set the continuous innovation intensity to

$$\lambda=p_6/\delta=\chi n,\qquad H=T\delta.$$

`n` is the share of normalized labor assigned to research and `chi` is the assumed research productivity. Under fixed controls,

$$E[\log A_H-\log A_0]=H\chi n\log(1+q)=T p_6\log(1+q).$$

This matches one expected-log growth moment. It does not make Bernoulli rounds and a Poisson arrival process identical. Their expected quality levels differ:

$$E[A_T]/A_0=(1+qp_6)^T\quad\hbox{versus}\quad E[A_H]/A_0=\exp(q\lambda H).$$

Also distinguish a **frozen research control** from a market that implements its stationary target. During a market transition research can vary, so its cumulative gain need not exactly equal the frozen-control static gain.

## 3. Who the two groups are and how needs evolve

The groups are illustrative populations with different exposure and recovery rates. They are not “China versus Germany,” employers versus workers, or empirically identified social classes. The current reference uses equal group weights for average needs and lost productive capacity.

With a unit normalized labor endowment, define manufacturing labor and output as

$$m=1-ha-\kappa(u_A+u_B)/2-n>0,\qquad Y=A m^\theta.$$

`ha` is labor used for assistance. `kappa` converts unfinished adjustment into a temporary productive-capacity loss. Research also takes labor from current production. The shared trained-labor constraint is

$$0\leq a\leq1,\qquad n\geq0,\qquad n+ha\leq B.$$

`B` is available research/assistance capacity. It is not the observed R&D expenditure/GDP ratio. Observed resource ratios enter a conditional conversion and one-moment match under assumed wage, production and time parameters; they do not identify actual research labor, `chi`, the innovation jump, or welfare weights.

For each group,

$$\dot u_g=d_g\chi n(1-a)(1-u_g)-(r_{0g}+r_{1g}a)u_g,\qquad g\in\{A,B\}.$$

New innovations expose some members who have not already developed needs. Assistance reduces entry into needs and raises recovery; baseline recovery works without additional help. At zero needs, entry is nonnegative; at complete exposure, recovery reduces needs. The states therefore stay in `[0,1]` under admissible controls.

R3's declared group parameters are `d = (0.75,0.38)`, `r0 = (0.12,0.32)` and `r1 = (1.2,1.0)`. Group A is more exposed and recovers more slowly in the reference. These values need empirical validation. Common aid is applied to both groups; this implementation does not optimize separate group-specific transfers.

Implementation: `model.py: active_labor, production, burden_flow, burden_step`.

## 4. What the patent price means

The patent value is the value of the currently leading innovation's future monopoly profits until a replacement destroys those rents. It is a model asset value, normalized by the current technology scale, not a price taken from a real patent registry. It is distinct from the modeled intermediate-good price.

The Cobb–Douglas monopoly core uses normalized wage and profit

$$w=\theta^2m^{\theta-1},\qquad \pi=\theta(1-\theta)m^\theta.$$

The normalized patent value `v` satisfies

$$\dot v=(\rho+\chi n)v-\pi.$$

At an interior free-entry research allocation,

$$\chi\gamma v=(1-\sigma)w.$$

`sigma` is the research subsidy; a negative value is a tax. If the potential return does not cover research costs, the zero-research corner is possible. At the research capacity boundary, a positive entry gap can remain because additional trained labor is unavailable. These corners require inequalities rather than a falsely universal equality.

A human/GPT rule specifies assistance and a target stationary research share `n* = p6/(delta chi)`. A derived tax/subsidy implements that target. For an interior target,

$$\sigma^*=1-\frac{\chi\gamma\pi^*}{(\rho+\chi n^*)w^*}.$$

The aid and incentive stay fixed for each advice rule while the market's research and patent valuation evolve. Its path is selected by a future valuation boundary condition. This is a conditional policy implementation; the planner's full transition has not been shown to have a complete fiscal/market implementation.

Implementation: `model.py: market_steady, market_allocation, market_path`; `node2.py: adj_subsidy`.

## 5. Exactly what the dynamic planner optimizes

For a declared discount rate `rho` and need penalty `omega`, the planner chooses research and assistance as functions of the current need state:

$$
J=\max_{n(\cdot),a(\cdot)}E\int_0^\infty e^{-\rho t}A_t
\left[m_t^\theta-\omega\max\{u_A(t),u_B(t)\}\right]dt.
$$

It values current production and the future production made possible by innovation. It explicitly penalizes the worse group's unfinished adjustment. Research can improve tomorrow's technology while reducing today's production and increasing needs. Aid can relieve needs while consuming labor that could otherwise support research or production.

The reference values `rho = 0.10` and `omega = 0.30` are assumptions. The latter converts a need share into an output-equivalent penalty. For example, lowering the worse group's needs by ten percentage points reduces the instantaneous penalty by `0.30 × 0.10 = 0.03` output units per unit of technology. This states the ethical trade-off explicitly; the survey audit does not select it. Because `A` scales both terms, absolute need penalties grow with technology. That proportionality is also a declared modeling choice.

**Worked feasible choice.** In the Germany reference scenario, take `uA = 0.10`, `uB = 0.05`, `n = 0.03`, `a = 0.50`. With `h = 0.04` and `kappa = 0.18`, manufacturing labor is `0.9365`, output per unit technology is approximately `0.93958`, and the need penalty is `0.03`. Instantaneous welfare per unit technology is approximately `0.90958`. The research/aid use is `0.05` of normalized labor, below the cap `B ≈ 0.09023`. This is one admissible choice, not the optimal policy.

An objective called “welfare” remains conditional on its units, penalty and institutional interpretation. The planner does not maximize every plotted outcome simultaneously. Even `omega = 0` can favor aid because needs reduce productive capacity.

## 6. The formal state-dependent rule and its numerical implementation

Write `V(A,u) = A v(u)` and `f(u,n,a)` for the two need-flow equations. The ideal continuous-time equation is

$$\rho v(u)=\max_{(n,a)\in\mathcal A(u)}\left\{m^\theta-\omega\max_g u_g+\nabla v(u)\cdot f(u,n,a)+q\chi n\,v(u)\right\}.$$

The innovation term is `q chi n v`, because a success multiplies the technology-scaled value by `1+q`. Using `log(1+q)` here would substitute a different objective. A sufficient finite-value condition is

$$\rho>q\chi B.$$

All current reference and displayed `q` scenarios pass it. The unchecked original uncapped linear-utility configuration can have unbounded value; a finite numerical array does not repair that problem. The cap is an explicit extension.

The supplied implementation uses a finite decision interval, state grid and action menu. Between decisions, it holds the chosen controls fixed. Its one-step rule is

$$
(n_k,a_k)\in\arg\max_{(n,a)\in\mathcal A_{61}}
\left\{\int_0^{\Delta t}e^{-(\rho-q\chi n)s}
\left[m_s^\theta-\omega\max_g u_g(s)\right]ds
+e^{-(\rho-q\chi n)\Delta t}\mathcal I[v](u(\Delta t))\right\}.
$$

Here `I[v]` interpolates the stored value between need-state grid points. At the actual state each decision interval, the code compares 61 assistance choices and 61 fractions of remaining research capacity. It selects a maximizing action and holds it for `dt = 0.125`. The reference grid has 101 points per need dimension. It interpolates **values**, then re-optimizes; it does not simulate by interpolating a discontinuous control surface.

The solver's reward integration uses three-point quadrature, action re-evaluation uses five points, and rollout metric integration uses seven. Fifteen tested off-grid states select the same action across the first two choices; the audit does not assume this proves exact agreement everywhere. Finite state/action grids, quadrature, interpolation and decision intervals remain numerical approximations.

“Optimal” should therefore mean a numerical solution of the declared discounted decision problem under these assumptions and discretizations. It should not mean a verified global continuous-control optimum, an empirically estimated national policy, or a rule that dominates all growth and equity measures.

Implementation: `control.py: BellmanSolver`; `node2_diagnostics.py: HeldPolicy.action, rollout, metrics`.

## 7. What growth and equality-risk measurements mean

For innovations arriving at intensity `chi n`, cumulative expected log-quality gain and expected technology-level growth differ:

$$G(H)=\int_0^H\log(1+q)\chi n(t)dt,\qquad E[A_H]/A_0=\exp\!\left(\int_0^H q\chi n(t)dt\right).$$

The reported `g_log = G(H)/H` is an average rate, and `g(t) = log(1+q) chi n(t)` is an instantaneous rate. `G(t)` is cumulative progress. If needs and research settle while research stays positive, the rate becomes constant and cumulative progress continues to rise. Technology is not stationary merely because normalized need states are stationary.

In the worked Germany choice above, the instantaneous expected-log rate is approximately `0.00762` per model time unit, whereas the expected-level growth rate is approximately `0.00792`. Neither is an observed annual growth rate. The clock has not been calibrated to a year.

Reported need metrics are

$$U_g(H)=H^{-1}\int_0^H u_g(t)dt,\quad \bar U=(U_A+U_B)/2,\quad U^{\max}=\max\{U_A,U_B\}.$$

The objective instead penalizes `max(uA(t),uB(t))` at each instant, with technology and discount weighting. **They are not the same measurement.** Suppose A has all the needs for the first half and B for the second half. The time-average instantaneous maximum is one, while the maximum group-average is one half. State both definitions.

Lower unresolved needs indicate one aspect of adjustment and equity risk. These measures do not give a Gini coefficient, wage equality or a complete distribution of benefits. Mean expected output includes the modeled labor and capacity costs; environmental impacts and observed livelihood outcomes are not measured.

## 8. How to compare the rules fairly

For any outcome `M`, define the matched within-country version change and its change in distance from human advice:

$$\Delta_{\rm upgrade}M=M_{56}-M_{55},\qquad
\Delta_{\rm reference}|M|=|M_{56}-M_h|-|M_{55}-M_h|.$$

The first asks what the update changes in the model. The second asks whether it becomes closer to the human-rule outcome. They can answer differently. Fix physical parameters, initial states, the human-reference profile, horizon and general mapping. Allow aid and the derived tax/subsidy to change as the specified implementation of each rule.

The planner is a separate normative institution and should be compared separately. The no-R&D-tax/subsidy market benchmark retains human-rule aid. All R3 policies face the same capacity cap within a country, but do not spend the same amount. This differs from the earlier tipping experiment's exact-spending comparison.

For country comparisons, resource-based scenario parameters differ as well as answer profiles. For a weight or innovation-size sensitivity, change only that parameter within a country and re-optimize the planner. A `q` scan is an economic innovation-size experiment, not a GPT upgrade experiment. Report matching state/action/time discretizations and check finite-value and drastic-innovation conditions.

**Verified focal results.** On the matched market comparison at horizon 100, GPT-5.6 minus GPT-5.5 changes cumulative `G` by approximately `-0.002699` in China, `-0.001946` in Germany and `-0.004009` in Egypt. Worst-group time-average needs change by approximately `-0.0313`, `-0.0288` and `-0.0323` percentage points. The growth deviations from the human-rule baseline become larger. These are conditional transformations of archived answers, not identified national effects.

The planner optimizes an infinite-horizon objective while plotted path summaries use horizon 100. Its value-consistency check includes a continuation value after that horizon. A comparison of truncated welfare alone is not automatically a comparison of the optimizer's complete objective.

## 9. The earlier tipping rule, retained as an alternative

To preserve the earlier extension, state its separate assumption explicitly:

$$\nu=2.4(1-a)=0.94\,\nu_{\rm fold}(a,\widehat c).$$

The estimated fold solves `F = 0` and `Fz = 0` in the earlier coordination model. The adviser reserves six percent below that perceived local boundary. An incorrect channel estimate can make the chosen speed exceed the actual boundary. The rule is a heuristic about branch existence, not a welfare optimum or a guarantee that all starting states recover.

A separate 181-point exact-spending menu chooses the greatest growth among candidates satisfying `gT ≥ 0.10`, worst-group average exposure `≤ 0.50` and final adoption `≥ 0.50`. The attained point is best on that menu. The channel weights, objective thresholds and margin are declared choices. They are distinct from R3's `omega`, labor cap and state-dependent optimization.

## 10. Short main-text wording ready for adaptation

We study a transparent institution that turns the same six response signals into innovation and assistance choices, first using the human-reference profile and then each model's profile. The institution is specified rather than estimated; human advice supplies a reference, not an assumed social optimum. Within each country scenario, technology, initial needs, resources and the decision mapping are held fixed, so the comparison traces the conditional consequences of replacing the adviser.

Research improves future technologies while using people who could produce today and creating demands for adjustment. Assistance also uses labor, but prevents some needs and helps recovery. We extend a creative-destruction economy with two illustrative groups whose exposure and recovery rates differ. A separate planner revises research and assistance as their needs change, maximizing expected discounted production minus a declared penalty on the worse group's unresolved needs. The penalty states a social trade-off in output units; it is not inferred from the six survey items.

The simulations therefore ask three distinct questions: whether the model represents the reference answers more faithfully, whether its advice moves closer to the reference rule, and how that advice changes growth and adjustment under the specified economy. These questions need not give the same ranking. Their connection offers a testable mechanism for studying accountable AI advice in innovation-driven transitions.
