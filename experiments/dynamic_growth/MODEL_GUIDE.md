# How the dynamic mechanism works

The experiment asks whether an adviser that misreads values selects a
technology rollout that the actual system can sustain. Survey and archived
model answer shares supply the representation-error inputs. Economic
coefficients, response weights, cultural-change laws, and policy objectives
are declared assumptions in `parameters.json`.

## Two adjustment groups

Groups A and B are equally weighted illustrative populations facing
different adjustment processes. For the same technology replacement rate,
A enters unresolved adjustment faster (0.75 versus 0.38), recovers more
slowly without assistance (0.12 versus 0.32), and responds more strongly to
additional assistance (1.20 versus 1.00). They are synthetic groups with
explicit parameters. The equity-risk measures report each group's exposure,
their average, the more exposed group, and their gap.

## Innovation, coordination, and exposure

Coordination is the state `z`. Adoption is `x = sigmoid(2z)`. Potential
launch intensity `nu` and adoption determine successful replacement:

    arrival = nu * x
    dq/dt = log(1.12) * arrival
    du_g/dt = d_g * arrival * (1 - u_g) - (r0_g + r1_g * aid) * u_g
    dz/dt = b*z - z^3 + 0.70 + culture + 0.45*aid - 0.90*nu - 0.35*mean(u_g)

`q` is accumulated log frontier quality. `u_g` is the group's share still
facing adjustment. Replacement adds exposure; recovery and assistance
remove it. With `b = 1`, coordination reinforces itself and can permit a
sharp adoption loss. The separate `b = -1` control restores coordination
and has a unique attracting equilibrium.

Holding cultural distributions constant keeps the `culture` input fixed.
Innovation can continue: positive replacement raises accumulated `q` even
when values do not change. The growth outcome is the change in `q` divided
by the horizon. Figure growth values multiply it by 100. Time is normalized
adjustment time, with horizon 60; it is not calendar years.

## Full answer distributions and adviser beliefs

The response channel sums changes in expected directed item coordinates,
using six declared weights: `0.20, 0.20, 0.15, -0.15, 0.10, 0.20` for
Q48, Q57, Q106, Q108, Q121, and Q159. Absolute weights sum to one.
Linear, saturating, and spline responses and four strengths are compared.
A restricted-item control retains Q48/Q57/Q159 and renormalizes their weights.
Zero response strength is an exact null. The 47 answer-category slots
retain six valid probability distributions throughout cultural change.

The actual cultural channel and the adviser's estimate are separate.
Belief errors change the selected policy; the shared actual equations
determine its consequences. Countries identify where error vectors came
from. Every vector is evaluated in the same hypothetical economy.

## The policy rule and resource constraint

Assistance `aid` and launch intensity share one normalized budget:

    aid >= 0
    nu >= 0
    aid + nu / 2.40 <= 1

The reference and optimistic advisers both exhaust that budget. Each
chooses the assistance level where the exact-spending line intersects
94% of its estimated upper fold intensity. The remaining 6% is a declared
branch-existence margin. This is a specified decision heuristic.

A separate search compares 181 exact-spending assistance allocations
between zero and 0.90. It selects the highest growth among candidates with
growth at least 0.10, worst-group average exposure at most 0.50, and final
adoption at least 0.50. It establishes the best candidate on that finite
menu. These constraints are normative research choices requiring practical
validation and community deliberation. The broader attainable-set figure
uses 1,378 feasible assistance/intensity pairs.

## Changing values and outdated advice

Five probability-preserving families compare unchanged values, gradual
drift, responses to experienced exposure, interaction between groups, and
memory with a temporary shock. The rate/delay experiment changes cultural
speed and the lag in updating advice. The rollout experiment instead
holds opportunity endpoints fixed while varying rollout speed and the
additional assistance allocation under exact equal spending.

The 2.5% assistance result describes three admitted speeds on a seven-speed
grid under all three criteria. Greater assistance can preserve adoption
while missing the growth floor. Both effects remain in the released data.

## Sources and the next evidence

[SOURCES.md](SOURCES.md) distinguishes the innovation-growth foundations,
mathematics, implementation, and related applications. Decision experiments
can estimate institutions' response rules. Longitudinal community-validated
surveys and adoption/livelihood panels can estimate cultural change,
coordination, exposure, and recovery. Environmental and income outcomes
would extend the current quality and exposure measures.
