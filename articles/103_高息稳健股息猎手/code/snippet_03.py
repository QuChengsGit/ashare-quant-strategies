def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    df = get_fundamentals(query(valuation.code).filter(valuation.code.in_(stocks)).order_by(valuation.market_cap.asc()))
    choice = list(df.code)
    choice = filter_st_stock(choice)
    choice = filter_paused_stock(choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    choice = choice[:g.stock_num]
    cdata = get_current_data()
    for s in context.portfolio.positions:
        if (s not in choice):
            log.info('Sell', s, cdata[s].name)
            order_target(s, 0)
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        psize = context.portfolio.available_cash/(g.stock_num - position_count)
        for s in choice:
            if s not in context.portfolio.positions:
                log.info('buy', s, cdata[s].name)
                order_value(s, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break
