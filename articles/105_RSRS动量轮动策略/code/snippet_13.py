def get_timing_signal(context, stock):
    data = attribute_history(stock, g.M[stock] + g.N[stock], '1d', ['high', 'low', 'close'])
    data['pre_close'] = data.shift(periods=1)['close']
    data['ret'] = data['close'] / data['pre_close'] - 1
    ret_std = data['ret'].rolling(g.N[stock]).std()
    ret_quantile = ret_std.tail(g.M[stock]).rank(pct=True)[-1]
    intercept, slope, r2 = get_ols(data.tail(g.N[stock]).low, data.tail(g.N[stock]).high)
    slope_series = [get_ols(data.low[i:i+g.N[stock]], data.high[i:i+g.N[stock]])[1] for i in range(g.M[stock])]
    slope_series.append(slope)
    zscore = get_zscore(slope_series[-g.M[stock]:])
    rsrs_score = zscore * r2**(2 * ret_quantile)
    if rsrs_score > g.score_threshold[stock]: return "BUY"
    elif rsrs_score < -g.score_threshold[stock]: return "SELL"
    else: return "KEEP"

复制
