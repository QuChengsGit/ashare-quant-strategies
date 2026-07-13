def trade(context):
    end_date = context.previous_date
    current_data = get_current_data()
    # 获取所有股票代码
    stocks = get_all_securities('stock', end_date).index.tolist()
    # 基本财务指标筛选
    q = query(
        valuation.code
    ).filter(
        valuation.code.in_(stocks),
        valuation.pb_ratio > 0,
        indicator.inc_return > 0
    )
    stocks = list(get_fundamentals(q).code)
    # 根据股息率筛选
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.1)[:100]
    # 进一步过滤风险股
    stocks = [
        stock for stock in stocks if not (
            current_data[stock].paused or
            current_data[stock].is_st or
            ('ST' in current_data[stock].name) or
            ('*' in current_data[stock].name) or
            ('退' in current_data[stock].name) or
            (current_data[stock].last_price == current_data[stock].high_limit) or
            (current_data[stock].last_price == current_data[stock].low_limit)
        )
    ]
    # 限制最终股票数量
    stocks = stocks[:g.stocknum]
    # 调整持仓
    for s in context.portfolio.positions:
        if s not in stocks:
            order_target(s, 0)
    psize = context.portfolio.total_value / g.stocknum
    for s in stocks:
        if len(context.portfolio.positions) >= g.stocknum:
            break
        if s not in context.portfolio.positions:
            order_value(s, psize)
    record(stocknum=len(context.portfolio.positions))
