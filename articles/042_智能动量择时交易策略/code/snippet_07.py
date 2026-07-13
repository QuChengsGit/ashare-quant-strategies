def initial_slope_series():
    length = g.N + g.M + g.K
    data = attribute_history(g.ref_stock, length, '1d', ['high', 'low', 'close'])
    multe_data = [get_ols(data.low[i:i + g.N], data.high[i:i + g.N]) for i in range(length - g.N)]
    slopes = [i[1] for i in multe_data]
    r2s = [i[2] for i in multe_data]
    zscores = [(get_zscore(slopes[i + 1:i + 1 + g.M]) * r2s[i + g.M]) for i in range(g.K)]
    return slopes, zscores
def initial_stock_motion(stock_pool):
    stock_motion = {}
    for stock in stock_pool:
        motion_que = []
        data = attribute_history(stock, g.biasN + g.momentum_day + 1, '1d', ['close'])
        data = data[:-1]
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]  # 乖离因子
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000  # 乖离动量拟合
        motion_que.append(score)
        stock_motion[stock] = motion_que
    return stock_motion

复制
