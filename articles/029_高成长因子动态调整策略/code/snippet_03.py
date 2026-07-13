def market_opened(context):
    if g.is_empty_position == False:
        adjustment(context, context.previous_date)

def adjustment(context, yesterday):
    all_stocks = list(get_all_securities(types=['stock'], date=yesterday).index)
    g.buy_list = basic_filters(context, all_stocks)  # 基础过滤
    g.buy_list = get_high_growth_stocks(context, g.buy_list)[:g.total_stock_num * 2]  # 获取高增长股票池
    recent_limit_up_list = get_recent_limit_up_stock(context, g.buy_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    g.buy_list = [stock for stock in g.buy_list if stock not in black_list]  # 过滤黑名单中的股票
    g.buy_list = filter_limitup_stock(context, g.buy_list)[:min(g.total_stock_num, len(g.buy_list))]  # 过滤涨停股票
    # 卖出不在买入列表中的股票
    for stock in context.portfolio.positions:
        if stock not in g.buy_list and stock not in g.high_limit_list:
            limit_price = get_current_data()[stock].last_price * 0.9
            order_target(stock, 0, MarketOrderStyle(limit_price))
            log.info("日常调仓卖出[%s]" % (stock))
    # 购买新的股票
    no_hold_target_num = g.total_stock_num - len(context.portfolio.positions)
    if no_hold_target_num > 0:
        cash_per_stock = context.portfolio.available_cash / no_hold_target_num
        for stock in g.buy_list:
            if stock not in g.hold_list:
                limit_price = get_current_data()[stock].last_price * 1.1
                order_target_value(stock, cash_per_stock, MarketOrderStyle(limit_price))
