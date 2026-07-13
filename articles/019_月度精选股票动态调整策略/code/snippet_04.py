def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    stocks = filter_st_stock(stocks)
    stocks = filter_new_stock(context, stocks)
    stocks = choice_try_A(context, stocks)
    stocks = filter_paused_stock(stocks)
    stocks = filter_limit_stock(context, stocks)[:g.stock_num]
    cdata = get_current_data()
    slist(context, stocks)
    # 卖出不在新筛选列表中的股票
    for s in context.portfolio.positions:
        if s not in stocks and cdata[s].last_price < cdata[s].high_limit:
            log.info('Sell', s, cdata[s].name)
            order_target(s, 0)
    # 买入新选中的股票
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        psize = context.portfolio.available_cash / (g.stock_num - position_count)
        for s in stocks:
            if s not in context.portfolio.positions:
                log.info('Buy', s, cdata[s].name)
                order_value(s, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break
