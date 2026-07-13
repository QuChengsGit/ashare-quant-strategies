def prepare_stocks(context):
    if len(context.portfolio.positions) >= g.max_hold_num:
        g.prepare_stocks = []
        log.info("满仓中")
        return
    date = transform_date(context.previous_date, 'str')
    initial_list = prepare_stock_list(date)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(
        valuation.code.in_(initial_list), valuation.circulating_market_cap < 25)
    df = get_fundamentals(q)
    lst = list(df['code'])
    lst = get_hl_stock(lst, date, 300)
    lst = get_no_hl_stock(lst, date, 30)
    lst = filter_amp(lst, date, 15)
    df = upward(lst, date, 15)
    lst = list(df.index)
    lst = approaching_max(lst, date, 60)
    g.prepare_stocks = lst

复制
