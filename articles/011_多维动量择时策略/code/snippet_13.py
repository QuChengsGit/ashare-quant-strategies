def get_rank(context, stock_pool):
    rank = []
    for stock in stock_pool:
        data = attribute_history(stock, g.biasN + g.momentum_day, '1d', ['close'])
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000
        adr = 100 * (data.close[-1] - data.close[-2]) / data.close[-2]
        rank.append([stock, score, adr])
        g.stock_motion[stock].append(score)
        if len(g.stock_motion[stock]) > 5:
            g.stock_motion[stock].pop(0)
    rank = [i for i in rank if not math.isnan(i[1])]
    rank.sort(key=lambda x: x[1], reverse=True)
    return rank[0]

复制
