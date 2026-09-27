# Statistical analysis appendix: 64-country paired comparison

## Design

The paired experiment contains 64 countries, six World Values Survey anchors,
two model identifiers, and five requested generations per
country–question–model cell: $64\times6\times2\times5=3,840$ valid final
responses. China is included. Venezuela is the sole country from the
65-country human derivative excluded because Q159 is missing. Generations are
averaged within a cell; the country is the inferential unit.

Primary uncertainty uses 20,000 country-bootstrap draws with BCa intervals and
19,999 paired country sign flips. Monte Carlo SEs are released. Global metrics
use Holm correction across five outcomes. Item claims use a single
dependence-preserving max-$T$ family across all six questions and both W1 and
TVD, rather than two easier within-metric families.

## Global estimates and contrasts

Negative target-loss contrasts favor GPT-5.6 Sol.

| Metric | GPT-5.5 (SE) | GPT-5.6 (SE) | Contrast (SE) | 95% BCa CI | Holm p |
|---|---:|---:|---:|---:|---:|
| W1 | 0.1284 (0.0052) | 0.1265 (0.0050) | -0.0020 (0.0011) | [-0.0040, 0.0003] | 0.3190 |
| TVD | 0.3124 (0.0092) | 0.3043 (0.0088) | -0.0080 (0.0014) | [-0.0107, -0.0050] | 0.00025 |
| CRG | 1.0469 (0.0449) | 1.0447 (0.0448) | -0.0022 (0.0117) | [-0.0243, 0.0215] | 0.8446 |
| $|\mathrm{VDR}-1|$ | 0.4127 | 0.3907 | -0.0220 (0.0135) | [-0.0506, 0.0025] | 0.3190 |
| $1-\mathrm{CSR}$ | 0.6789 | 0.7122 | 0.0333 (0.0232) | [-0.0082, 0.0834] | 0.3190 |

The global corrected conclusion is a reduction in TVD. The other four
contrasts are uncertain; their intervals are not evidence of equivalence.

## Joint item family

Three of 12 contrasts cross the familywise 5% threshold:

| Distance and item | Contrast | SE | Simultaneous 95% CI | max-$T$ p |
|---|---:|---:|---:|---:|
| W1, Q108 responsibility | -0.00824 | 0.00250 | [-0.01563, -0.00086] | 0.01735 |
| TVD, Q106 income distribution | -0.02661 | 0.00418 | [-0.03892, -0.01430] | 0.00005 |
| TVD, Q108 responsibility | -0.02070 | 0.00319 | [-0.03009, -0.01131] | 0.00005 |

Q106 W1 (p=0.05915) and Q159 TVD (p=0.05580) narrowly miss the joint
threshold and are not reported as confirmed gains. The complete 12-row table
is `joint_item_inference.csv`.

## Repeated-generation composition

For five observed generation distributions with mean $\bar p$, squared error
obeys

$$E_K=\|\bar p-q\|^2+\frac{5-K}{4K}\,V,$$

where $V$ is the observed generation-varying component. Averaging all five
generations removes 1.180% (95% BCa CI [1.018%, 1.371%]) of GPT-5.5 error and
1.313% [1.147%, 1.509%] of GPT-5.6 error. GPT-5.6 has a lower shared error
floor by -0.00633 [-0.00834, -0.00452], while its change in the
generation-varying component is uncertain: 0.00007 [-0.00004, 0.00018].

## Spatial robustness

The primary graph is a symmetric row-standardized four-nearest-neighbor graph
using great-circle distances. Six- and eight-neighbor graphs and spatial-HAC
cutoffs of 1,000, 2,000, 3,000, and 5,000 km are sensitivity checks.

- At $k=4$, the global TVD spatial-error estimate is -0.00809 (SE 0.00197;
  95% CI [-0.01195, -0.00424]; 14-outcome Holm p=0.00047). Results remain
  below zero at $k=6$ and $k=8$.
- At 1,000 km, global TVD spatial-HAC is -0.00805 (SE 0.00158; 95% CI
  [-0.01119, -0.00490]; 15-outcome Holm p=0.000042); all four cutoffs retain
  the conclusion.
- Global TVD's Moran statistic is 0.1436 (raw p=0.0326) but does not survive
  the 27-outcome BH family (q=0.1085). CRG change has Moran $I=0.2245$
  (q=0.0594) and Geary $C=0.7521$ (q=0.0324).

These are one-wave cross-sectional diagnostics. They do not identify temporal
diffusion, cultural spillovers, or a causal regional process. Expected
near-constant-input warnings in some spatial-error auxiliary diagnostics are
retained in logs; the reported coefficients and covariance estimates complete.

## Creative-destruction margins

Mean squared TVD is grouped into declared issue pairs:

| Margin | GPT-5.5 | GPT-5.6 | Contrast (SE) | 95% BCa CI | Holm p |
|---|---:|---:|---:|---:|---:|
| Opportunity/participation | 0.15467 | 0.15000 | -0.00467 (0.00144) | [-0.00753, -0.00190] | 0.00350 |
| Distribution/adjustment | 0.17839 | 0.15706 | -0.02133 (0.00260) | [-0.02638, -0.01614] | 0.00015 |
| Coordination/legitimacy | 0.03588 | 0.03826 | 0.00238 (0.00127) | [-0.00005, 0.00492] | 0.06710 |

Across 1,326 nonnegative weight combinations in 0.02 steps, 88.76% of paired
95% intervals favor GPT-5.6, 11.24% are uncertain, and none favor GPT-5.5.
This is an exploratory sensitivity over a declared index, not an estimate of
economic decisions, policy effects, growth, or welfare.

## Reproducibility boundary

All statistics, result tables, and figures rebuild offline from frozen
outputs. A later live request to the undated GPT-5.6 Sol serving identifier is
not guaranteed to return the same answers.
