def my_Trader(context):
    # 获取上一个交易日的所有股票列表
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    # 过滤掉科创板、北交所、ST股票
    stocks = filter_kcbj_stock(stocks)
    stocks = filter_st_stock(stocks)
    # 筛选财务指标优秀的股票
    df = get_fundamentals(query(
            valuation.code
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,  # 市净率 > 0
            indicator.inc_return > 0,  # 净资产收益率增长率 > 0
            indicator.inc_total_revenue_year_on_year > 0,  # 营业收入同比增长 > 0
            indicator.inc_net_profit_year_on_year > 0,  # 净利润同比增长 > 0
            indicator.ocf_to_operating_profit > 5  # 经营活动现金流/经营利润 > 5%
        ).order_by(
            valuation.market_cap.asc()  # 按市值升序排序
        ).limit(g.stock_num))  # 限制选股数量
    # 获取最终选择的股票
    choice = list(df.code)
    # 卖出不符合条件的股票
    for stock in context.portfolio.positions:
        if stock not in choice and stock not in g.high_limit_list:
            order_target(stock, 0)
    # 计算每只股票的目标仓位
    psize = context.portfolio.total_value / g.stock_num
    # 买入新的股票
    for stock in choice:
        if context.portfolio.available_cash < psize:
            break
        if stock not in context.portfolio.positions:
            order_value(stock, psize)
