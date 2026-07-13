def get_index_signal(index_pool):
    score_list = []
    for index in index_pool:
        data = attribute_history(index, g.momentum_day, '1d', ['low'])
        y = np.log(data.low)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        annualized_returns = math.pow(math.exp(slope), 250) - 1
        r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
        score = annualized_returns * r_squared
        score_list.append(score)
    index_dict = dict(zip(index_pool, score_list))
    best_index = sorted(index_dict.items(), key=lambda item: item[1], reverse=True)[0][0]
    return best_index

复制
