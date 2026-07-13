def monthly_adjustment(context):
    target_list = get_stock_list(context)  # 获取目标股票列表
    target_list = filter_paused_stock(target_list)
    target_list = filter_limit_stock(context, target_list)
    # 卖出不在目标列表中的股票
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
            log.info(f"卖出[{stock}]")
            position = context.portfolio.positions[stock]
            close_position(position)
    # 买入新的目标股票
    position_count = len(context.portfolio.positions)
    target_num = g.stock_num
    if target_num > position_count:
        value = context.portfolio.available_cash / (target_num - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) >= g.stock_num:
                        break

复制
