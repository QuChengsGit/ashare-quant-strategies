def get_signal():
    close_data = attribute_history(g.stock, g.mean_day + g.mean_diff_day, '1d', ['close'])
    today_MA = close_data.close[g.mean_diff_day:].mean()
    before_MA = close_data.close[:-g.mean_diff_day].mean()
    data = attribute_history(g.stock, g.N, '1d', ['high', 'low'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    if rsrs_score > g.score_threshold and today_MA > before_MA:
        return "BUY"
    elif rsrs_score < -g.score_threshold and today_MA < before_MA:
        return "SELL"
    else:
        return "KEEP"
