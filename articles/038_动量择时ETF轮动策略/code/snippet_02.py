def get_rank(etf_pool):
    score_list = []
    for etf in etf_pool:
        df = attribute_history(etf, g.m_days, '1d', ['close'])
        y = df['log'] = np.log(df.close)
        x = df['num'] = np.arange(df.log.size)
        slope, intercept = np.polyfit(x, y, 1)
        annualized_returns = np.exp(slope) ** 250 - 1
        r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
        score = annualized_returns * r_squared
        # 反转因子调整
        df2 = attribute_history(etf, g.m_days * 8, '1d', ['close'])
        y2 = df2['log'] = np.log(df2.close)
        x2 = df2['num'] = np.arange(df2.log.size)
        slope2, intercept2 = np.polyfit(x2, y2, 1)
        annualized_returns2 = np.exp(slope2) ** 250 - 1
        r_squared2 = 1 - (sum((y2 - (slope2 * x2 + intercept2))**2) / ((len(y2) - 1) * np.var(y2, ddof=1)))
        score -= annualized_returns2 * r_squared2 / 6
        score_list.append(score)
    df = pd.DataFrame({'score': score_list}, index=etf_pool)
    df = df.sort_values(by='score', ascending=False)
    return df
