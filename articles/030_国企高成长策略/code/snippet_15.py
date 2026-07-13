def weekly_adjustment(context):
    g.target_list = filter_paused_stock(g.target_list)
    g.target_list = filter_limitup_stock(context, g.target_list)
    g.target_list = filter_limitdown_stock(context, g.target_list)
    black_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)
    g.target_list = [stock for stock in g.target_list if stock not in black_list]
    # 卖出不符合条件的股票
    for stock in g.hold_list:
        if stock not in g.target_list and stock not in g.high_limit_list:
            close_position(stock)
    # 买入新的股票
    position_count = len(context.portfolio.positions)
    if position_count < g.stock_num:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in g.target_list:
            if stock not in context.portfolio.positions.keys():
                if open_position(stock, value):
                    if len(context.portfolio.positions) >= g.stock_num:
                        break

复制
