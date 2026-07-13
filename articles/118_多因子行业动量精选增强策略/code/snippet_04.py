def standardize_factors(factors):
    zscore = (factors - factors.mean()) / factors.std()
    return zscore.fillna(0)
