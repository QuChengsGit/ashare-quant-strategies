# 获取反转因子评分
def get_reversal_score(etf, lookback_days):
    df = attribute_history(etf, lookback_days, '1d', ['close'])
    log_returns = np.log(df['close'])
    days = np.arange(log_returns.size)
    # 线性回归计算年化收益率和R方
    slope, intercept = np.polyfit(days, log_returns, 1)
    annualized_returns = np.exp(slope * 250) - 1
    r_squared = 1 - (np.sum((log_returns - (slope * days + intercept))**2) / ((len(log_returns) - 1) * np.var(log_returns, ddof=1)))
    return annualized_returns * r_squared

复制
