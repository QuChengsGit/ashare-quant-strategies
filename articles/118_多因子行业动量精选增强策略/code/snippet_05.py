def compute_composite_score(factors, weights):
    score = (factors * weights).sum(axis=1)
    return score.sort_values(ascending=False)
