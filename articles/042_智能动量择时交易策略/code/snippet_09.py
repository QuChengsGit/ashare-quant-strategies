def get_rank(context, stock_pool):
    rank = []
    for stock in stock_pool:
        data = attribute_history(stock, g.biasN + g.momentum_day, '1d', ['close'])
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000  # 乖离动量拟合
        adr = 100 * (data.close[-1] - data.close[-2]) / data.close[-2]  # 股票的涨跌幅度
        raise_x = g.SwitchFactor if stock == g.hold_stock else 1
        rank.append([stock, score * raise_x, adr])
        g.stock_motion[stock].append(score)
        if len(g.stock_motion[stock]) > 5:
            g.stock_motion[stock].pop(0)
    rank = [i for i in rank if not math.isnan(i[1])]
    rank.sort(key=lambda x: x[1], reverse=True)
    return rank[0]
def get_timing_signal(context, stock):
    data = attribute_history(g.ref_stock, g.N, '1d', ['high', 'low', 'close'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    g.rsrs_score_history.append(rsrs_score)
    rsrs_slope = get_zscore_slope(g.rsrs_score_history[-g.K:])
    idex_slope = np.polyfit(np.arange(8), data.close[-8:], 1)[0].real
    g.slope_series.pop(0)
    g.rsrs_score_history.pop(
0)
    log.info('rsrs_slope {:.3f}'.format(rsrs_slope) + ' rsrs_score {:.3f} '.format(rsrs_score) + ' idex_slope {:.3f} '.format(idex_slope))
    WR2, WR1 = WR([g.ref_stock], check_date=context.previous_date, N=21, N1=14, unit='1d', include_now=True)
    if WR1[g.ref_stock] >= 97 and WR2[g.ref_stock] >= 97:
        return "BUY"
    if rsrs_slope < 0 and rsrs_score > 0:
        return "SELL"
    if idex_slope < 0 and rsrs_slope > 0 and rsrs_score < g.score_fall_thr:
        return "SELL"
    if idex_slope > g.idex_slope_raise_thr and rsrs_slope > 0:
        return "BUY"
    if rsrs_score > g.score_thr:
        return "BUY"
    else:
        return "SELL"

复制
