def before_market_open(context):
    g.check_out_lists = []
    current_data = get_current_data()
    check_date = context.previous_date - datetime.timedelta(days=200)
    all_stocks = list(get_all_securities(date=check_date).index)
    # 过滤创业板、ST、停牌、涨停、跌停股票
    all_stocks = [stock for stock in all_stocks if not (
        (current_data[stock].day_open == current_data[stock].high_limit) or  
        (current_data[stock].day_open == current_data[stock].low_limit) or  
        current_data[stock].paused or  
        current_data[stock].is_st or  
        ('ST' in current_data[stock].name) or
        ('*' in current_data[stock].name) or
        ('退' in current_data[stock].name) or
        (stock.startswith(('30', '68', '8', '4')))
    )]
    # 多因子筛选
    q = query(
        valuation.code, valuation.market_cap, valuation.pe_ratio, income.total_operating_revenue
    ).filter(
        valuation.pb_ratio < 1,
        cash_flow.subtotal_operate_cash_inflow > 1e6,
        indicator.adjusted_profit > 1e6,
        indicator.roa > 0.15,
        indicator.inc_net_profit_year_on_year > 0,
        valuation.code.in_(all_stocks)
    ).order_by(
        indicator.roa.desc()
    ).limit(
        g.buy_stock_count * 3
    )
    check_out_lists = list(get_fundamentals(q).code)
    g.check_out_lists = check_out_lists[:g.buy_stock_count]
    log.info("今日股票池：%s" % g.check_out_lists)
