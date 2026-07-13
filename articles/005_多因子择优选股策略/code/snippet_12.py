def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    # 限制持仓数量
    target_list = target_list[:min(g.stock_num, len(target_list))]
    # 调整持仓，卖出不在目标列表中的股票
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.yesterday_HL_list:
            log.info(f"卖出[{stock}]")
            close_position(context.portfolio.positions[stock])
    # 买入目标列表中的股票
    position_count = len(context.portfolio.positions)
    target_num = len(target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == target_num:
                        break

复制
