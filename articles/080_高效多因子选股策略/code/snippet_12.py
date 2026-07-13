def adjust_position(context):
    # 获取应买入列表
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    target_list = target_list[:min(g.stock_num, len(target_list))]
    # 排除黑名单股票
    target_list = [stock for stock in target_list if stock not in g.black_list]
    # 调仓卖出
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
            position = context.portfolio.positions[stock]
            close_position(position)
    # 调仓买入
    for stock in target_list:
        if context.portfolio.positions[stock].total_amount == 0:
            value = context.portfolio.cash / (len(target_list) - len(context.portfolio.positions))
            open_position(stock, value)

复制
