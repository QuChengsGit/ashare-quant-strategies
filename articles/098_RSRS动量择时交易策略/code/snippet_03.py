def get_rank(context, stock_pool):
    rank = []
    for stock in g.stock_pool:
        data = attribute_history(stock, g.momentum_day, '1d', ['close'])
        data.close = data.close / data.close[0]
        pred_data = kalman_filter(np.array(data.close), 0.15)
        score = np.polyfit(np.arange(20), pred_data[-20:], 1)[0]
        rank.append([stock, score])
    rank.sort(key=lambda x: x[-1], reverse=True)
    return rank[0]
