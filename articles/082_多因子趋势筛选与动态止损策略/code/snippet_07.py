def select_stocks(context, stocklist):
    # 根据趋势过滤股票
    stocklist = get_trend_filter(context, stocklist, context.previous_date, g.short_duration, '1d', g.trend_up, g.trend_down)
    # 涨幅过滤
    if 'R' in g.pool_filter:
        stocklist = get_rise_filter(context, stocklist, g.index, g.short_duration, g.rise_uplimit)
    # 按照持仓数量选取股票
    if g.stocknum == 0 or len(stocklist) <= g.stocknum:
        return stocklist
    else:
        return stocklist[:g.stocknum]
