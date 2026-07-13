def initial_slope_series():
    length = g.N + g.M + g.K
    data = attribute_history(g.ref_stock, length, '1d', ['high', 'low', 'close'])
    multe_data = [get_ols(data.low[i:i + g.N], data.high[i:i + g.N]) for i in range(length - g.N)]
    slopes = [i[1] for i in multe_data]
    r2s = [i[2] for i in multe_data]
    zscores = [(get_zscore(slopes[i + 1:i + 1 + g.M]) * r2s[i + g.M]) for i in range(g.K)]
    return slopes, zscores
def get_ols(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return intercept, slope, r2
def get_zscore(slope_series):
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std
def get_zscore_slope(z_scores):
    y = z_scores
    x = np.arange(len(z_scores))
    slope, intercept = np.polyfit(x, y, 1)
    return slope
def get_timing_signal(context, stock):
    data = attribute_history(g.ref_stock, g.N, '1d', ['high', 'low', 'close'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    g.rsrs_score_history.append(rsrs_score)
    rsrs_slope = get_zscore_slope(g.rsrs_score_history[-g.K:])
    idex_slope = np.polyfit(np.arange(8), data.close[-8:], 1)[0].real
    g.slope_series.pop(0)
    g.rsrs_score_history.pop(0)
    log.info(f'rsrs_slope: {rsrs_slope:.3f}, rsrs_score: {rsrs_score:.3f}, idex_slope: {idex_slope:.3f}')
    if rsrs_slope < 0 and rsrs_score > 0:
        return "SELL"
    if idex_slope < 0 and rsrs_slope > 0 and rsrs_score < g.score_fall_thr:
        return "SELL"
    if idex_slope > g.idex_slope_raise_thr and rsrs_slope > 0:
        return "BUY"
    if rsrs_score > g.score_thr:
        return "BUY"
    return "SELL"
