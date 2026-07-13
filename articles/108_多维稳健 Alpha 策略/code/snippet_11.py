def weekly_adjustment(context):
    g.target_list = get_stock_list(context)[:10]  # 获取前10只符合条件的股票
    g.target_list = filter_paused_stock(g.target_list)  # 过滤停牌股票
    g.target_list = filter_limitup_stock(context, g.target_list)  # 过滤涨停股票
    g.target_list = filter_limitdown_stock(context, g.target_list)  # 过滤跌停股票
    recent_limit_up_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)  # 获取最近有涨停的股票
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))  # 排除黑名单中的股票
    g.target_list = [stock for stock in g.target_list if stock not in black_list]  # 过滤掉黑名单中的股票
    g.target_list = g.target_list[:min(g.stock_num, len(g.target_list))]  # 限制最多持仓的股票数
    # 卖出不符合条件的股票
    for stock in g.hold_list:
        if stock not in g.target_list and stock not in g.high_limit_list:
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
    # 买入符合条件的股票
    position_count = len(context.portfolio.positions)
    target_num = len(g.target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)
        for stock in g.target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == target_num:
                        break

复制
