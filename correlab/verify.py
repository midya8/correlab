"""Replay a fixed-law audit without calling the production obedience engine.

The verifier enumerates every complete deviation map, then reconstructs all
reported terms and aggregates. Input parsing alone is shared with the package.
"""
from fractions import Fraction as F
from itertools import product
from .exact import matrix, jsonify


def _replay_player(payoff, joint, player):
    m, n = len(joint), len(joint[0])
    size = m if player == 'row' else n
    cells = [(i, j) for i in range(m) for j in range(n)]
    own = (lambda i, j: i) if player == 'row' else (lambda i, j: j)
    other = (lambda i, j: j) if player == 'row' else (lambda i, j: i)

    def difference(i, j, action):
        changed = payoff[action][j] if player == 'row' else payoff[i][action]
        return changed - payoff[i][j]

    baseline = sum(joint[i][j] * payoff[i][j] for i, j in cells)
    maps = list(product(range(size), repeat=size))
    scores = [sum(joint[i][j] * difference(i, j, action_map[own(i, j)])
                  for i, j in cells) for action_map in maps]
    scores_by_map = dict(zip(maps, scores))
    best = max(scores)
    optimal = [action_map for action_map, score in zip(maps, scores) if score == best]
    chosen = optimal[0]
    masses = [sum(joint[i][j] for i, j in cells if own(i, j) == rec)
              for rec in range(size)]
    internal = []
    for rec in range(size):
        deviations = []
        for action in range(size):
            # Column records use opponent rows in ascending order, just as row
            # records use opponent columns. This is output order, not a transpose.
            terms = [{'opponent_action': other(i, j), 'probability': joint[i][j],
                      'payoff_difference': difference(i, j, action),
                      'contribution': joint[i][j] * difference(i, j, action)}
                     for i, j in cells if own(i, j) == rec]
            action_map = list(range(size))
            action_map[rec] = action
            gain = scores_by_map[tuple(action_map)]
            deviations.append({'recommendation': rec, 'deviation': action,
                               'mass': masses[rec], 'weighted_gain': gain,
                               'conditional_gain': gain / masses[rec] if masses[rec] else None,
                               'terms': terms})
        internal.append(deviations)
    coarse = []
    for action in range(size):
        gain = scores_by_map[(action,) * size]
        coarse.append({'deviation': action,
                       'by_recommendation': [internal[rec][action]['weighted_gain']
                                             for rec in range(size)],
                       'gain': gain, 'deviating_payoff': baseline + gain})
    raw = max(record['gain'] for record in coarse)
    pairwise = max(record['weighted_gain'] for row in internal for record in row)
    conditional = max(record['conditional_gain'] for row in internal for record in row
                      if record['conditional_gain'] is not None)
    # Reorder column cell witnesses by own recommendation, then opponent action.
    ordered = sorted(cells, key=lambda ij: (own(*ij), other(*ij)))
    witness = [{'recommended_action': own(i, j), 'opponent_action': other(i, j),
                'chosen_action': chosen[own(i, j)], 'probability': joint[i][j],
                'payoff_difference': difference(i, j, chosen[own(i, j)]),
                'contribution': joint[i][j] * difference(i, j, chosen[own(i, j)])}
               for i, j in ordered]
    return {'player': player, 'expected_payoff': baseline,
            'recommendation_masses': masses, 'coarse_deviations': coarse,
            'coarse_max_raw_gain': raw,
            'coarse_best_actions': [r['deviation'] for r in coarse if r['gain'] == raw],
            'external_regret': max(F(0), raw), 'internal_deviations': internal,
            'pairwise_internal_regret': pairwise, 'worst_conditional_gain': conditional,
            'swap_regret': best,
            'optimal_swap_choices': [sorted({action_map[rec] for action_map in optimal})
                                     for rec in range(size)],
            'optimal_swap_count': len(optimal), 'attaining_swap': list(chosen),
            'attaining_swap_cells': witness, 'attaining_swap_payoff': baseline + best,
            'is_cce_obedient': raw <= 0, 'is_ce_obedient': pairwise == 0}


def _replay(a, b, q):
    m, n = len(q), len(q[0])
    x = [sum(row) for row in q]
    y = [sum(q[i][j] for i in range(m)) for j in range(n)]
    independent = [[x[i] * y[j] for j in range(n)] for i in range(m)]
    players = [_replay_player(a, q, 'row'), _replay_player(b, q, 'column')]
    return {'shape': [m, n], 'row_payoffs': a, 'column_payoffs': b, 'joint': q,
            'marginals': {'row': x, 'column': y}, 'product_joint': independent,
            'is_product': q == independent,
            'total_variation_from_product': sum(abs(q[i][j] - independent[i][j])
                                                for i in range(m) for j in range(n)) / 2,
            'players': players,
            'cce_epsilon': max(p['external_regret'] for p in players),
            'ce_pairwise_epsilon': max(p['pairwise_internal_regret'] for p in players),
            'ce_swap_epsilon': max(p['swap_regret'] for p in players),
            'ce_conditional_epsilon': max(p['worst_conditional_gain'] for p in players),
            'is_cce': all(p['is_cce_obedient'] for p in players),
            'is_ce': all(p['is_ce_obedient'] for p in players),
            'is_nash_product': q == independent and all(p['is_cce_obedient'] for p in players)}


def verify_audit(report):
    """Return bounded mismatch paths for a complete fixed-law audit.

    Native Fraction-valued reports and their JSON-decoded form are accepted.
    A valid result means internal arithmetic consistency for the embedded inputs,
    not authenticity, equilibrium search, or truth about agents outside the table.
    """
    mismatches = []
    try:
        if not isinstance(report, dict):
            raise ValueError('report must be an object')
        a, b, q = (matrix(report[key]) for key in ('row_payoffs', 'column_payoffs', 'joint'))
        shape = (len(a), len(a[0]))
        if any((len(v), len(v[0])) != shape for v in (b, q)):
            raise ValueError('embedded matrix shapes differ')
        if any(v < 0 for row in q for v in row) or sum(map(sum, q)) != 1:
            raise ValueError('embedded joint law is not a probability distribution')
        expected = _replay(a, b, q)
        expected['product_control'] = _replay(a, b, expected['product_joint'])
        expected, observed = jsonify(expected), jsonify(report)

        def compare(want, got, path):
            if len(mismatches) >= 20:
                return
            if type(want) is not type(got):
                mismatches.append(path + ': type')
            elif isinstance(want, dict):
                if want.keys() != got.keys():
                    mismatches.append(path + ': keys')
                for key in want:
                    if key in got:
                        compare(want[key], got[key], path + '.' + key)
            elif isinstance(want, list):
                if len(want) != len(got):
                    mismatches.append(path + ': length')
                for index, (left, right) in enumerate(zip(want, got)):
                    compare(left, right, path + '[' + str(index) + ']')
            elif want != got:
                mismatches.append(path + ': value')

        compare(expected, observed, '$')
    except (KeyError, ValueError, TypeError, RecursionError) as error:
        mismatches = ['invalid report: ' + str(error)]
    return {'valid': not mismatches, 'model': 'fixed-law-bimatrix-obedience',
            'mismatches': mismatches,
            'scope': 'arithmetic consistency of the complete report and its embedded inputs only'}
