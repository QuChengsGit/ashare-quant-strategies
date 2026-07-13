def weekly_adjustment(context):
    g.target_list = get_stock_list(context)[:g.stock_num + 5]
    g.target_list = filter_paused_stock(g.target_list)
    g.target_list = filter_limitup_stock(context, g.target_list)
    g.target_list = filter_limitdown_stock(context, g.target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    g.target_list = [stock for stock in g.target_list if stock not in black_list]
    g.target_list = g.target_list[:min(g.stock_num, len(g.target_list))]
    for stock in g.hold_list:
        if (stock not in g.target_list) and (stock not in g.high_limit_list):
            position = context.portfolio.positions[stock]
            close_position(position)
    position_count = len(context.portfolio.positions)
    if len(g.target_list) > position_count:
        value = context.portfolio.cash / (len(g.target_list) - position_count)
        for stock in g.target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == len(g.target_list):
                        break

复制
