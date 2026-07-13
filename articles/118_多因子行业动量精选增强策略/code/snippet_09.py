def compute_portfolio_weights(selected_stocks):
    n = len(selected_stocks)
    return {s: 1.0 / n for s in selected_stocks}
