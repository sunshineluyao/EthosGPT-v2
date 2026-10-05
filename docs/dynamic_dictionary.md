# Dictionary for the dynamic growth and adjustment study

These definitions accompany [the model guide](../experiments/dynamic_growth/MODEL_GUIDE.md). [The primary-source guide](../experiments/dynamic_growth/SOURCES.md) explains the role of each economic, mathematical, and numerical source.

| Term | Meaning in this study |
|---|---|
| Marginal distribution | Answer shares for one question, summing to one. It does not identify how one person answers several questions together. |
| Joint distribution | Probabilities for combinations of answers across questions. It is not reconstructed from the six marginal profiles. |
| Probability simplex | The set of nonnegative category shares that sum to one. Remaining on it means retaining valid distributions. |
| Directed category score $r_{jk}$ | A category position on $[-1,1]$ after the declared question-specific direction. It describes a response scale, not a ranking of cultures. |
| Actual values $p$ | The full response distributions used by the actual transition equations. In static error comparisons they equal the survey anchor. |
| Estimated values $\widehat p$ | The distributions described by the AI adviser. Their difference from $p$ is the representation error. |
| Response channel $H$ | The stated rule that converts full distributions into one input to coordination. Its weights, strength, and curvature are assumed. |
| Response strength $\kappa$ | How strongly differences in answer shares affect that channel; dimensionless. Zero gives an exact no-response control. |
| Linear response | Equal answer-score changes have equal marginal influence throughout the scale. |
| Saturating response | Influence flattens toward endpoints, so additional changes have smaller marginal influence there. |
| PCHIP / cubic response | A smooth piecewise cubic curve through stated knots that preserves their monotone direction; an alternative assumed response. |
| Exponential tilt | A normalized redistribution that multiplies each initial share by an exponential score factor, keeping valid answer shares. |
| Markov drift | Gradual probability flow toward a specified target; the rate determines the speed, not a demographic fact about the survey countries. |
| Replicator feedback | A mass-preserving rule in which categories with above-average assumed responses gain share; here the responses depend on experienced exposure. |
| Group interaction | Exchange of answer shares between two illustrative groups, represented by a symmetric diffusion term. |
| Memory $m_g$ | A smoothed record of a group's exposure, with adjustment time eight; it is not a measured psychological trait. |
| Shock | A temporary change of the stated cultural target from time 20 to 30. The model tracks subsequent adjustment. |
| Adviser lag $L$ | Time between the actual distribution and the distribution used to select advice; normalized time units. |
| Creative destruction | Quality-improving innovation replaces established activities, connecting productive opportunity with social adjustment. |
| Quality ladder | A sequence of better technologies; each successful replacement multiplies quality by $\gamma=1.12$ here. |
| Coordination $z$ | A dimensionless state representing how readily the transition can sustain adoption. It is an assumed state, not a survey factor score. |
| Adoption $x(z)$ | A share between zero and one derived smoothly from coordination; higher $z$ gives higher adoption. |
| Potential intensity $\nu$ | Opportunities for successful replacement per normalized time before applying the adoption share. |
| Arrival intensity $\lambda$ | Successful replacements per normalized time, $\lambda=\nu x(z)$. It differs from the speed at which an opportunity path changes. |
| Rollout rate $r$ | How rapidly the opportunity or cultural path moves between identical endpoints. Its inverse relates to transition duration. |
| Equilibrium | A state that remains unchanged with fixed policy and cultural conditions. |
| Attracting / stable state | A state toward which sufficiently small disturbances decay; stability is local unless a wider claim is proved. |
| Unstable state | A state with at least one direction in which a small disturbance grows. |
| Feedback | A consequence returns to affect the process that produced it. Reinforcing and restoring feedback imply different transition behavior. |
| Fold / turning point | An attracting and an unstable equilibrium meet as a parameter varies; a high-adoption branch can cease to exist. |
| Bifurcation | A qualitative change in the available states or their stability as a parameter varies. |
| Jacobian $J$ | The matrix of first derivatives describing how small changes in each state alter every state's rate of change. |
| Eigenvalue / mode | A local rate and direction of disturbance evolution. Negative real parts indicate decay; a zero mode marks the reported folds. |
| Continuation | Following an equilibrium curve through parameter space, including parts that a time trajectory would not approach. |
| Pseudo-arclength | Following distance along that curve rather than insisting that one parameter always increases; this passes turning points. |
| Basin of attraction | Initial states that approach the same outcome. The teaching figure uses a finite-horizon classification. |
| Nullcline | A curve along which one state's rate of change is zero; its intersections are candidate equilibria in a phase plane. |
| Rate-induced tipping | Fast change prevents tracking of a continuing stable state, even though that state never disappears. |
| Cusp normal form | A simple analytic equation whose two fold boundaries meet. The example teaches the concept; no economic cusp is identified. |
| Normalized time $t,T$ | A model adjustment scale, with horizon $T=60$; it is not calendar years. |
| Mean log quality $q$ | The expected log-quality index accumulated through successful replacements. It differs from the log of expected quality. |
| Dynamic efficiency $g_T$ | Change in mean log quality divided by time. Higher indicates faster improvement; figures use $100g_T$ log-quality points per time unit. |
| Earlier efficiency $G_T$ | Expected frontier-quality gain after a stated number of discrete rounds. Its denominator and units differ from $g_T$. |
| Unresolved exposure $u_g$ | The group share facing unfinished adjustment at a particular time; it need not equal observed unemployment. |
| Group-average exposure $U_{g,T}$ | The time integral of $u_g$ divided by the horizon; a share between zero and one. |
| Average exposure $\bar U_T$ | The mean of the two group-average exposures, using equal group weights. |
| Worst-group exposure $U_T^{\max}$ | The larger group-average exposure. It asks whether aggregate progress leaves one group with a heavier burden. |
| Exposure gap | The absolute difference between the two group averages; an equity-risk diagnostic rather than an income-inequality index. |
| Final adoption $x(T)$ | Adoption at the end of the comparison. It tests persistence that favorable average outcomes can conceal. |
| Assistance allocation $a$ | The share of one normalized resource budget supporting recovery and coordination. |
| Additional aid $\delta$ | Resources diverted from launch capacity to assistance during rollout, with the resulting intensity reduction explicitly paid for. |
| Attainable set / frontier | Outcomes achievable under feasible policies in the actual system; beliefs select a point without changing the shared actual set. |
| Admissibility | Meeting declared growth, worst-group exposure, and final-adoption criteria. It expresses chosen objectives, not a universal welfare judgment. |
| Finite-menu optimum | The best of the specified evaluated policies; it need not be the best policy among all continuous or time-varying choices. |
| Balanced growth | Capital and technology maintain a constant ratio; it does not imply equal income growth across groups. |
| Capital ratio $k=K/A$ | Physical capital divided by technology, in normalized units, used in the separate closed-resource benchmark. |
| Resource closure | Consumption, policy spending, and investment sum to output. Aid is not financed by an unrecorded subsidy. |
| Calibration / identification | Calibration sets parameters using external evidence; identification establishes which data distinguish a mechanism. The new response coefficients are not identified by this audit. |
| Conditional mechanism result | A computed consequence of measured error inputs and stated assumptions, which supplies a hypothesis for empirical tests. |
| Null or reversed result | A comparison with no effect or an effect opposite to a proposed general pattern; both are retained to delimit the mechanism. |
