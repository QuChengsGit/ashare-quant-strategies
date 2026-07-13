def get_timing_signal(context, stock):
    data = attribute_history(g.ref_stock, 18, '1d', ['high', 'low'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    log.info('rsrs_score {:.3f}'.format(rsrs_score))
    if rsrs_score > g.score_threshold: return "BUY"
    elif rsrs_score < -g.score_threshold: return "SELL"
    else: return "KEEP"
