def get_socre(stock):
    data = attribute_history(stock, g.momentum_day, '1d', ['close'])
    y = data['log'] = np.log(data.close)
    x = data['num'] = np.arange(data.log.size)
    slope, intercept = np.polyfit(x, y, 1)
    annualized_returns = math.pow(math.exp(slope), 250) - 1
    r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return annualized_returns * r_squared
