def apply_transaction_costs(prev_weights, new_weights, cost_rate=0.001):
    turnover = sum(abs(new_weights.get(s, 0) - prev_weights.get(s, 0)) for s in set(prev_weights) | set(new_weights))
    cost = turnover * cost_rate
    return max(1 - cost, 0)
