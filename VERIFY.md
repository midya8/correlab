# Replay a fixed-law report

`verify_audit(report)` checks a complete `audit` result using an independent arithmetic route. It accepts the native report, whose rational values are Fractions, or the JSON-decoded report, whose rational values are strings. It returns a validity flag and at most 20 mismatch paths.

This verifier covers the original fixed-law bimatrix audit and its product-marginals control. It does not verify history, private-signal, garbling or partition reports. Those commands retain their existing tests and complete-output checks.

## Separate calculation

The production engine finds the best swap separately for each own recommendation. The verifier instead enumerates every complete action map, at most `4^4=256` maps per player. It directly sums the payoff change over the original joint cells for each map. No production obedience function is called or imported. Only the bounded exact-input parser and rational-to-JSON conversion are shared.

For each player, the replay reconstructs:

- Every map score, the maximum score, the first maximizing map in lexicographic order, the exact maximizing-map count and all per-recommendation optimal choices.
- Every constant-map gain and every single-recommendation deviation, including all cell terms, zero-mass null conditional values and exact ties.
- Baseline payoff, full witness cells, expected payoff after the chosen map, the four regret conventions and both obedience flags.

The complete joint report is then rebuilt: marginals, their product, total variation, the four maximum incentives and the equilibrium flags. The verifier repeats the calculation for the different product-marginals law. Column-player contributions use the original row/column tables directly, rather than the production engine's transpose route. Both players maximize their own payoff tables.

All dictionary keys, list lengths, field types and values must match. A boolean is not accepted in place of an integer, nor is an integer accepted in place of a rational string in a serialized report. Fractions in a native report are normalized to the same rational-string representation before comparison. The dictionary's insertion order does not matter; list order does, because action indices and witness order carry meaning. Mismatch paths follow the expected field order, and the diagnostic list is capped at 20.

## Run

```python
from correlab import audit, verify_audit

report = audit([[2,0],[0,1]], [[2,0],[0,1]],
               [['1/2',0],[0,'1/2']])
assert verify_audit(report)['valid']
```

```sh
python -m correlab audit examples/audit-input.json > /tmp/report.json
python -m correlab verify /tmp/report.json
python -m correlab verify examples/verify-input.json
python examples/verify_wheel.py
```

The verify command prints a JSON result. Exit zero means consistent; exit one means an invalid or inconsistent report. Unreadable files, malformed JSON, duplicate keys, nonfinite constants, malformed UTF-8, parser-recursion failures or files over the existing 2 MB input limit exit two with empty stdout. No schema-version field is added to the existing report format. Unknown fields are rejected rather than silently ignored.

Embedded payoff and probability matrices use the existing parser: one to four actions per side, exact integers/Fractions/rational or decimal strings, no float or boolean values, at most 512-bit input rational components and 160-character input strings. The embedded joint law must normalize exactly and have the same shape as both payoff tables.

## Checks

Seven added tests cover 2,835 exact ternary 2x2 game/quarter-grid-law reports, 32 rectangular and larger cases up to four actions per side, and a zero-mass/tied control with 256 optimal maps. Four developed demo reports pass in native and JSON form while the production obedience functions are patched to fail if called.

A separate test changes every leaf of a complete developed report one at a time, including embedded inputs, hidden cell terms and the product control, and requires rejection. Additional controls remove keys, add fields, truncate witnesses, substitute field types and invalidate embedded laws. Input and output isolation, unchanged RNG state, deterministic bounded diagnostics and CLI exit distinctions are tested.

The full suite has 57 tests. The installed-wheel verifier runs all of them outside checkout, checks all eight package origins before and after, matches all eight complete module CLI outputs and regenerates both unchanged figures. The package has no console entry point. All seven original complete CLI outputs and both original SVG files are unchanged.

## What validity does not mean

This is internal arithmetic consistency for the report's embedded inputs. It is not a signature, a provenance check or proof that those inputs describe actual play. Someone can change the entire embedded problem and consistently rebuild the report; the verifier should accept that new problem. To bind a report to an external game or law, compare its embedded inputs with an independently trusted copy. Passing this checker does not establish equilibrium unless the corresponding verified flags say so.

The finite deviation-map definitions are standard. Enumeration is a separate implementation check, not a new equilibrium method or a scalable solver. No learner, training convergence, agent strength, privacy, simultaneous-override or statistical-generalization claim is made. Internal exact arithmetic may grow beyond the input component caps. See [DESIGN.md](DESIGN.md) for established definitions and original source attribution.
