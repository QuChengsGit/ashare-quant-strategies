def compute_industry_momentum(industry_prices, window=60):
    momentum = industry_prices.pct_change(window).iloc[-1]
    return momentum.sort_values(ascending=False)
