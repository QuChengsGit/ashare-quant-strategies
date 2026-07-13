def initial_stock_motion(stock_pool):
    stock_motion = {}
    for stock in stock_pool:
        motion_que = []
        data = attribute_history(stock, g.biasN + g.momentum_day + 1, '1d', ['close'])
        data = data[:-1]
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000
        motion_que.append(score)
        stock_motion[stock] = motion_que
    return stock_motion

复制
