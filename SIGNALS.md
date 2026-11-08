# Private override signals: information is part of the deviation model

Correlab v0.2 adds exact private-signal override certificates. It does **not**
silently relabel the original CE problem after hiding recommendations.

## Information and execution model

A trusted baseline executor draws `(i,j)` from the supplied joint law `Q` and
will execute those actions unless one player overrides. The row player sees
only a signal `z` from its supplied row-stochastic channel `K[i,z]`. It does
**not** also see `i`. It may choose `pass` (leave the hidden baseline action
unchanged), or override with any pure row action `d`. The opponent stays at its
baseline action. Audit the column player independently, using its own payoff
table, transposed orientation, and channel from `j` to its signal.

This is a unilateral decision problem with a state-dependent baseline pass
option. It is not a simultaneous override outcome, a new equilibrium concept,
a mediator design solver, or a model of what a real agent knows. With no
trusted executor, or if the baseline recommendation remains visible, this
information model does not apply. Channels depend only on own baseline action,
not on the opponent's action beyond correlation already in `Q`.

## Exact formula and witnesses

For the row player, define

```
m[z]   = sum_(i,j) Q[i,j] K[i,z]
H[z,d] = sum_(i,j) Q[i,j] K[i,z] (A[d,j] - A[i,j])
H[z,pass] = 0
V(K) = sum_z max_(pass,d) H[z,d]
```

Every candidate retains all `(i,j)` terms: joint probability, signal probability,
joint-signal mass, payoff difference and contribution. Conditional gain is
`H[z,d]/m[z]`, or JSON `null` when `m[z]=0`. A pass candidate has no changed
cells and an empty term list. Zero-mass signals still retain all other candidates
and all ties; they do not contribute to the gain. Signal policies are ordered
`pass, 0, ..., k-1` for deterministic tie-breaking. The report gives all optimal
choices per signal, their Cartesian-product count, the first attaining policy,
and its payoff `baseline + V(K)`. A randomized override policy cannot beat the
best pure policy: each signal's gain is linear in its choice probabilities.

### Endpoints and bounds

* Identity channel: `V(I)` is the original full-swap gain. A pass on a known
  recommendation is equivalent to staying, so it adds no value beyond swap.
* A constant signal, or any stochastic channel with identical rows:
  `V(K) = max(0, best fixed-action gain)`, the clipped coarse gain. Random noise
  cannot create useful information in this fixed decision problem.
* Every supplied channel satisfies `coarse_gain <= V(K) <= full_swap_gain`.
  The lower bound follows by using one fixed choice on all signals. For the
  upper bound, revealing the baseline action can simulate the channel first.
  Pure choices per revealed action are at least as good as that simulation.

These comparisons hold for the same baseline law and payoffs. They say nothing
about a changed equilibrium, welfare of simultaneous overrides, or whether
restricting information is desirable in an actual application.

## Supplied post-garbling certificate

A row-stochastic `L[z,t]` post-processes the observed signal, independently of
the state conditional on `z`. Its composite channel is

```
K'[i,t] = sum_z K[i,z] L[z,t]
```

The `garble` command retains both complete signal audits. It also lifts the
optimal coarse policy back to each original signal: draw `t` with `L[z,t]`,
then use the coarse policy's pass/override choice. Each original signal record
retains that choice distribution, all weighted gain terms, its lifted gain,
and the slack against the best original-signal choice. Thus

```
lifted_gain = V(K')
information_loss = V(K) - V(K') = sum_z optimality_slack[z] >= 0
```

This exact attaining lift is stronger evidence than a bare inequality check.
The result certifies **the supplied garbling only**. Correlab does not search
for an `L` linking arbitrary channels, establish a converse Blackwell order,
or infer such an order from equal values in one payoff problem. Equal value
in this game does not mean the signals are equally informative in every game.

## Deterministic partition audit

`partition_audit` lists all partitions of a player's baseline action set as
canonical restricted-growth label sequences, starting at 0. There are
`1, 2, 5, 15` for sizes `1, 2, 3, 4`. Each has its own complete signal audit.
The two players are audited separately, not as a cross-product of simultaneous
policies. Every strict refinement relation is retained as an index pair and
exact gain loss; these are **all** comparable pairs, not only Hasse-cover edges.
A fine partition can be deterministically mapped to a coarse one precisely
when equal fine labels imply equal coarse labels. No search over stochastic
channels or a global optimal privacy/obedience tradeoff is performed.

## Controls

The first control adapts the explicitly credited Roth game from v0.1. The
uniform diagonal baseline has payoff `3/10`, coarse gain `0`, full-swap gain
`11/30`. A channel emits a special signal only on baseline action C, with
probability `alpha`, otherwise a common signal. At `alpha = 0, 1/4, 1/2, 1`,
its override gains are exactly `0, 11/120, 11/60, 11/30`. This is a descriptive
change to a supplied information channel, not a learned intervention result.
The special signal is absent at alpha 0; its conditional gains are null.
Full identity signals garbled to an identical-row two-signal channel lose
`11/30` incentive value. The garbled optimal policy passes on both signals.

A developed asymmetric cyclic-payoff control uses row payoff table
`[[0,-10,3],[1,0,-10],[-10,2,0]]`, zero column payoffs, and the same uniform
diagonal joint law. Its five row partitions expose why the number of signals
alone does not determine incentive value:

| Own-action partition labels | Signals | Row override gain |
| --- | ---: | ---: |
| `[0,0,0]` | 1 | 0 |
| `[0,0,1]` | 2 | 4/3 |
| `[0,1,0]` | 2 | 5/3 |
| `[0,1,1]` | 2 | 1 |
| `[0,1,2]` | 3 | 2 |

Column override gain is zero throughout. The three two-signal partitions are
incomparable by refinement. These values do not order them for all decision
problems. Both controls use deterministic supplied tables and laws, not data.

## API and CLI

```python
from correlab import signals, garble, partition_audit, signal_demo
signals(row_payoffs, column_payoffs, joint, row_channel, column_channel)
garble(row_payoffs, column_payoffs, joint, row_channel, column_channel,
       row_garbling, column_garbling)
partition_audit(row_payoffs, column_payoffs, joint)
signal_demo()
```

```
python -m correlab signal-demo
python -m correlab signals examples/signals-input.json
python -m correlab garble examples/garble-input.json
python -m correlab partitions examples/partitions-input.json
python examples/render_signals.py --check
```

`signals-input.json` reveals C with probability 1/2, giving `11/60` gain.
`garble-input.json` then replaces either signal with an independent fair bit,
giving zero gain and information loss `11/60`. Input keys are strict. Channels
and garblings have 1..4 rows and 1..4 columns; row count must match their input
alphabet. All probabilities are exact, nonnegative, and every row sums to one.
The v0.1 rational, game-size and 2 MB CLI input bounds still apply. Do not pass
binary floats. Output retains witnesses and is intentionally not compact.

## Verification and attribution

An independent test enumerates all `(k+1)^s` signal-to-choice policies, including
pass, and scores them directly against `Q*K`, without the production optimizer.
It covers all 81 ternary 2x2 row-payoff tables and all 35 quarter-grid joint laws
under identity, constant and noisy channels (8,505 channel audits); the column
payoffs vary deterministically. It checks endpoint identities against v0.1.
Another 28 rectangular/larger cases enumerate four-signal policies, up to
625 policies per player. 243 supplied post-garbling cases check the lifted
policy and exact per-signal slack identity. All 16 pairs of original and garbled
signal counts 1..4 are additionally checked against independent composition,
full policy enumeration and direct joint-cell simulation of the lifted policy.
Other tests cover all partition
counts/refinements, known controls, unreachable signals, full ties, pass,
independent noise, positive scaling, payoff shifts, player exchange, composition,
no mutation, invalid channels, and strict CLI behavior. The figure binds its
numeric cells and complete compressed report to fresh calculations.

The implementation and controls are original code; the information-order
argument is standard, not a new theorem. Existing Roth fixture attribution
remains in [DESIGN.md](DESIGN.md). This extension uses these sources:

1. [Annie Liang, Comparing Information I, chapter 4](https://anniehliang.com/papers/lecture-notes/ch4.pdf): finite Markov channels, decision value and simulation proof (definitions 4.2-4.5, theorem 4.1). Her value subtracts the best uninformed action payoff; our gain subtracts the supplied executor baseline and includes pass. Do not equate these normalizations.
2. [Henrique de Oliveira, Blackwell's Informativeness Theorem Using Diagrams](https://henriquedeoliveira.com/wp-content/uploads/2020/12/blackwells-informativeness-theorem-using-diagrams.pdf), November 30, 2017 preprint: stochastic-map composition, lifted strategies, and the warning in section 6 that strategic information preferences are not automatically the single-agent order.
3. [Tilman Borgers, Notes on Blackwell Dominance](https://websites.umich.edu/~tborgers/BlackwellDominance.pdf), December 3, 2023: finite Markov experiments and the factorization criterion. The notes minimize losses; Correlab maximizes payoff gains.
4. [David Blackwell, Comparison of Experiments](https://www.degruyterbrill.com/document/doi/10.1525/9780520411586-009/html): original experiment comparison via attainable risk sets. Historical attribution only; no code is copied.
5. [Blackwell's informativeness theorem overview](https://en.wikipedia.org/wiki/Blackwell%27s_informativeness_theorem): secondary cross-check of the finite garbling and decision-value formulation, not the proof's sole source.
6. [Aaron Roth, AGT lecture 8](https://www.cis.upenn.edu/~aaroth/courses/slides/agt17/lect08.pdf): the original three-action coarse-versus-correlated fixture, adapted here only for the first control. Its conditional-regret display caveat is already documented in DESIGN.md.

The report makes only finite exact claims. No learned channel, Blackwell-order
search, entropy/mutual-information optimization, privacy guarantee, scalable
solver, equilibrium-welfare prediction or agent safety guarantee is included.
