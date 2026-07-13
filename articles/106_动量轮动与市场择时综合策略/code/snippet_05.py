def initial_slope_series():
    # 初始化前M日的斜率序列
    data = attribute_history('000300.XSHG', g.N + g.M, '1d', ['high', 'low'])
    return [get_ols(data.low[i:i+g.N], data.high[i:i+g.N])[1] for i in range(g.M)]
