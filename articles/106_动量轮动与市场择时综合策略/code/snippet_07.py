def get_timing_signal(stock, rank_stock_diff, context):
    # 计算RSRS和MA信号，判断是否买入、卖出或持仓
    close_data = attribute_history('000300.XSHG', g.mean_day + g.mean_diff_day, '1d', ['close'])
    today_MA = close_data.close[g.mean_diff_day:].mean()
    before_MA = close_data.close[:-g.mean_diff_day].mean()
    high_low_data = attribute_history('000300.XSHG', g.N, '1d', ['high', 'low'])
    intercept, slope, r2 = get_ols(high_low_data.low, high_low_data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2  # 修正标准分
    # 个股的择时判定
    stock_dif = rank_stock_diff.loc[stock]
    sig = np.sum((stock_dif < 0).astype(int))
    if sig < 2:
        return "BUY"
    elif sig >= 2:
        return "SELL"
    else:
        return "KEEP"
