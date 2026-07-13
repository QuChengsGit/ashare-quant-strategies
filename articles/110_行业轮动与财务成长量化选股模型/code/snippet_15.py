def weekly_adjustment(context):
    """
    每周调整持仓：卖出不在目标列表的股票，买入新的股票
    """
    target_stocks = get_stock_list(context)  # 获取目标股票列表
    # 卖出不在目标列表且不是昨日涨停的股票
    for stock in g.hold_list:
        if stock not in target_stocks and stock not in g.yesterday_HL_list:
            position = context.portfolio.positions[stock]
            close_position(position)
    # 计算并买入新的股票
    position_count = len(context.portfolio.positions)
    target_num = len(target_stocks)
    buy_num = min(target_num - position_count, g.stock_num)
    value = context.portfolio.cash / buy_num
    for stock in target_stocks:
        if stock not in context.portfolio.positions:
            if open_position(stock, value):
                if len(context.portfolio.positions) == target_num:
                    break

复制
