# Joint play, private advice and deviation certificates

## Problem and orientation

Correlab audits a supplied joint distribution Q on a finite two-player normal-form game. A[i,j] is the row player's payoff and B[i,j] is the column player's payoff. Both players maximize. Neither table is negated automatically; this is general-sum, unlike GameLab's row-max/column-min scalar zero-sum convention.

A mediator draws (i,j) from Q and privately recommends i to row and j to column. Each player knows Q and its payoff table, sees only its own recommendation, and assumes the other follows theirs. The audit measures unilateral incentives in that information model. It neither models messages between agents nor verifies an actual mediator, private-information game, mechanism, deployment or safety property.

All numbers use exact rational arithmetic. Every returned epsilon is in payoff units, not geometric distance to an equilibrium set, confidence, a p-value or a learning-rate guarantee.

## Three deviation families and four epsilon conventions

For row, let g(i,d) = sum_j Q[i,j] (A[d,j] - A[i,j]). This is the unconditional weighted gain from replacing recommendation i with action d and otherwise obeying. Each candidate retains its full opponent-action terms, probabilities, payoff differences and contributions. Column uses g(j,d) = sum_i Q[i,j] (B[i,d] - B[i,j]), with its own payoff table. No cancellation between the players is allowed.

### Coarse fixed-action deviations

A deviation to fixed d before seeing the recommendation has gain G(d) = sum_i g(i,d). A law is a coarse correlated equilibrium (CCE) precisely when every such gain for both players is at most zero.

`coarse_max_raw_gain` retains max_d G(d), which can be negative: obeying a correlated recommendation can beat every fixed action. `external_regret` is max(0, max_d G(d)), because opting not to deviate is always permitted. `cce_epsilon` is the maximum of those two clipped regrets. Each candidate's deviating payoff is baseline expected payoff plus G(d); all maximizing fixed-action ties are retained.

### One-pair internal deviations

`pairwise_internal_regret` is max_(i,d) g(i,d). Including d=i gives zero and makes this nonnegative. A law is a correlated equilibrium (CE) precisely when every g(i,d) is at most zero for both players. `ce_pairwise_epsilon` is the maximum of the two players' largest weighted pair gains.

### Full recommendation-dependent swap maps

A swap is any function f from own actions to own actions. Its gain is sum_i g(i,f(i)). Choices for distinct recommendations are unrestricted, so its exact maximum is sum_i max_d g(i,d). This separability avoids enumerating all k^k maps in production, while tests independently enumerate all maps, including 256 maps for four actions.

`swap_regret` is this maximum. `ce_swap_epsilon` is the maximum across players, not their sum. For each recommendation the report retains all maximizing actions; the Cartesian product gives every optimal swap, its cardinality is the product of tie counts, and the lexicographically first map is returned as an attaining witness. Every joint-cell contribution of that map is retained and sums exactly to the reported optimum. Zero-mass recommendations leave every action tied; they affect map count but not value.

For k own actions, external regret <= swap regret, pairwise regret <= swap regret <= k * pairwise regret. Exact zero pairwise and zero swap criteria coincide; positive epsilon conventions need not. Correlab names both instead of calling them interchangeable approximate CE errors. The three-recommendation control has pairwise gain 1/3 and full-swap gain 2/3.

### Conditional gains

If p_i = sum_j Q[i,j] > 0, conditional incentive is g(i,d)/p_i. If p_i = 0, conditional gain is `null`, not zero or division by zero; the weighted gain still equals zero. `worst_conditional_gain` and `ce_conditional_epsilon` maximize only over positive-mass recommendations and include stay actions. A law always has at least one such recommendation. The rare-recommendation control has weighted gain 1/1000 but conditional gain 1. A small unconditional epsilon does not promise small gains on all private signals.

These are different normalizations of explicitly listed deviation families. No approximate hierarchy is inferred from the exact-equilibrium hierarchy without the required action-count or mass factors.

## Correlation is part of the object

Marginals x and y do not determine Q. The audit retains x, y, their product P[i,j] = x[i] y[j], exact equality `is_product`, and total variation sum_(i,j) |Q[i,j]-P[i,j]| / 2. It separately audits P as `product_control`. This control is not an estimate, causal intervention or equivalent representation of Q.

In a product law, seeing one's own action gives no new information about the opponent. Product CCE is equivalent to mixed Nash; `is_nash_product` requires both product equality and CCE. A nonproduct CE is not labeled Nash merely because its marginals appear reasonable. The developed coordination control gives each player payoff 3/2 and swap regret zero under the diagonal law. Its product control pays 3/4 and has swap regret 1/4.

## Finite histories

`history` accepts realized joint actions in one fixed game, not changing payoff tables, mixed-strategy forecasts or bandit observations. At each requested checkpoint t it constructs exact counts N_t and Q_t = N_t/t, then returns the complete joint-law and product-control audit.

It also independently sums realized payoffs, each fixed-action counterfactual total, and the attaining swap's counterfactual total directly over the action sequence. The identities are:

- actual total = t * expected payoff under Q_t;
- clipped best-fixed counterfactual gain = t * external regret under Q_t;
- attaining-swap counterfactual gain = t * swap regret under Q_t.

The output retains those totals and maps. The final empirical law is order-invariant, while prefixes and the last-round law need not be. Replication scales totals and preserves final average audit values. The demo's final empirical law is CCE, but its last action pair has CCE epsilon 11/10. No implemented learner, no-regret theorem, expected-versus-realized concentration, asymptotic convergence, monotonic prefix improvement or last-iterate result is claimed.

## Input and output contract

The importable APIs are `audit(row_payoffs, column_payoffs, joint)`, `history(row_payoffs, column_payoffs, actions, checkpoints=None)`, and `demo()`.

Both payoff matrices and the joint law are rectangular, with matching shapes and one to four actions on each side. All probabilities must be nonnegative and sum exactly to one; no renormalization or epsilon tolerance is used. Exact values are Python integers, Fraction objects or strings matching `-?digits` optionally followed by `/digits` or `.digits`. Booleans, floats, exponent strings, plus signs, whitespace and nonfinite values are rejected. Strings are at most 160 characters; numerator/denominator inputs at most 512 bits. Intermediates may grow larger. Parsing copies inputs, never calls a random generator and makes no runtime network calls.

A history has 1..1000 joint action pairs with exact integer, non-boolean, in-range indices. Checkpoints, if given, are 1..100 strictly increasing round indices ending at the final round. The default is the final round alone. Full reports are verbose; checkpoint count is bounded to avoid accidental output blowups. These input caps are not scalability or latency guarantees.

CLI commands are `python -m correlab demo`, `audit FILE` and `history FILE`. The two input files are JSON objects with the API argument names, no unknown or missing keys. Only `checkpoints` is optional. Files are at most 2,000,000 bytes, UTF-8; duplicate object keys and NaN/Infinity are rejected. Errors exit two with empty stdout and a parser error on stderr. APIs reject invalid inputs with ValueError. Rational quantities serialize as canonical strings, structural counts/indices as integers, predicates as booleans, undefined conditional gains as null. The saved demo is the full report, not a summary. The installed wheel must match every full CLI output outside the checkout.

`audit` returns both payoff tables and the law, marginals/product/TV, two complete player audits, four named epsilon values, CCE/CE/product-Nash predicates and one nonrecursive `product_control`. Player audits contain every fixed and pairwise deviation, all swap-choice ties/count, one attaining map/cell witness and its payoff. `history` returns the realized sequence/checkpoints, count and full-audit reports, realized total certificates, and a separate complete last-round audit. No candidate is hidden because it makes a control look better.

## Verification and attribution

33 tests include 2,835 combinations of all 81 ternary 2x2 row payoff tables with 35 quarter-grid joint laws, paired with a separately varied column table, versus exhaustive swap-map and one-pair enumeration. Another 28 rectangular/larger controls enumerate every map, up to 256 per player. All 256 length-four histories in a 2x2 game are checked at three prefixes, including direct counterfactual identities. Positive affine player-specific transforms, transpose/player exchange, product Nash, negative raw coarse gains, zero-mass recommendations, 256 tied maps, replication, order changes, capacity, exact parsing, strict CLI and no-mutation/RNG checks are covered. Three SVG tests bind all 36 numeric cells, the complete compressed report, hidden-term tamper sensitivity and byte-exact regeneration. These are bounded deterministic controls, not benchmark evidence of agent strength.

This project implements established equilibrium/regret definitions, not a new algorithm or theorem. Six consulted sources:

1. [Avrim Blum and Yishay Mansour, Learning, Regret minimization, and Equilibria](https://www.cs.cmu.edu/~avrim/ML10/regret-chapter.pdf), textbook chapter, definitions 4.10/4.11 and theorem 4.12: single-pair versus full-swap regret, approximation convention and empirical-distribution identity. Some sections use losses; Correlab always uses payoff gains.
2. [University of Bonn, Correlated Equilibria, lecture 6](https://nerva.informatik.uni-bonn.de/lib/exe/fetch.php/teaching/ws2021/vl-agt/lecture06.pdf), teaching notes: conditional advice, nonproduct distributions, CE/CCE hierarchy and linear constraints. The notes use costs; inequalities reverse for this payoff-maximizing implementation.
3. [Aaron Roth, Algorithmic Game Theory, lecture 8](https://www.cis.upenn.edu/~aaroth/courses/slides/agt17/lect08.pdf), teaching notes: the 3x3 diagonal (1,1,-1.1) CCE-not-CE game and its uniform diagonal law are adapted directly, using exact -11/10. The source's displayed conditional formula has an unconditional left side; we use the surrounding prose, modification-rule definition and independent sources to condition both sides correctly. Other developed controls are separate small constructions, not external experimental data.
4. [Anas Barakat, Learning (Coarse)-Correlated Equilibria in General-Sum Games, lecture 10, October 16, 2025](https://learning-in-games.github.io/lect10-notes.pdf), preliminary teaching notes, definitions 1/5/11: constant versus arbitrary own-action transformations and product versus correlated laws. A later bullet repeats 'coarse' for arbitrary maps; Correlab follows the formal CE definition, cross-checked against Blum-Mansour, rather than that typo.
5. [Charles University, Algorithmic Game Theory tutorial 7](https://kam.mff.cuni.cz/~sychrovsky/AGT_2025/7/7.pdf), exercises/notes: weighted pairwise constraints and CE implies CCE. This source also uses costs, unlike our payoffs.
6. [Sergiu Hart and Andreu Mas-Colell, A Simple Adaptive Procedure Leading to Correlated Equilibrium, Econometrica 68(5), 2000](http://www.ma.huji.ac.il/~hart/papers/adapt.pdf), primary paper: private advice, empirical play and regret-based adaptation. Correlab does not implement or claim the paper's adaptive procedure or almost-sure convergence theorem.

Sources are technical primary teaching/textbook/paper material. No library implementation is imported. There is no general-sum equilibrium solver, trainer, scalable mechanism optimizer, hidden-information/extensive-form model, payoff-estimation guarantee, data collection, real-agent experiment or production-safety certification.
