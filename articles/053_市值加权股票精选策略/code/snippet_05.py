def rebalance(context):
    stocks = get_all_securities('stock').index.tolist()  # 获取所有股票列表
    stocks = filter_kcbj_stock(stocks)  # 过滤科创板和北交所股票
    stocks = filter_st_stock(stocks)  # 过滤ST及退市风险股票
    # 按市值升序选取市值最小的股票
    df = get_fundamentals(query(valuation.code, valuation.market_cap)
        .filter(valuation.code.in_(stocks))
        .order_by(valuation.market_cap.asc())
        .limit(g.stock_num))
    selected_stocks = list(df.code)  # 获取最终选中的股票代码
    # 卖出不再持有的股票
    for s in context.portfolio.positions:
        if s not in selected_stocks:
            order_target_value(s, 0)
    # 计算每只股票的目标持仓市值
    value_per_stock = context.portfolio.total_value / g.stock_num
    balance = {}
    for s in selected_stocks:
        if s in context.portfolio.positions:
            diff = value_per_stock - context.portfolio.positions[s].value
        else:
            diff = value_per_stock
        balance[s] = diff
    # 按需调整每只股票的持仓
    for s in dict(sorted(balance.items(), key=lambda x: x[1], reverse=False)).keys():
        order_target_value(s, value_per_stock)
    # 记录总市值变化
    total_market_cap = df.market_cap.sum()
    record(market_cap=total_market_cap)

复制
