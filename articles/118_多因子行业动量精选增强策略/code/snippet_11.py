def rebalance_portfolio(daily_data, prev_weights, industry_prices, stock_industry_map, factor_weights):
    industry_mom = compute_industry_momentum(industry_prices)
    top_industries = industry_mom.index[:3]

    stock_data = daily_data
    factors = compute_factors(stock_data)
    factors_std = standardize_factors(factors)
    composite_score = compute_composite_score(factors_std, factor_weights)

    industry_mask = industry_stock_filter(stock_industry_map, top_industries)
    selected_stocks = select_stocks(composite_score, industry_mask)

    base_weights = compute_portfolio_weights(selected_stocks)

    vol_scale = volatility_scaling(stock_data["Return"])
    scaled_weights = {s: w * vol_scale for s, w in base_weights.items()}

    tcost_multiplier = apply_transaction_costs(prev_weights, scaled_weights)
    final_weights = {s: w * tcost_multiplier for s, w in scaled_weights.items()}

    return final_weights
