def adjust_position(context, buy_stocks):
    # 清仓不在的股票
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
    # 平均分配资金
    position_count = len(context.portfolio.positions)
    if len(buy_stocks) <= position_count:
        return
    value = int(context.portfolio.cash / (len(buy_stocks) - position_count))
    value = min(value, g.max_cash)
    value = int(int(value / 100) * 100)  # 按100取整
    for stock in buy_stocks:
        if get_pos_amount(context, stock) != 0:
            continue
        data = attribute_history(stock, 1, '1m', ['close']).close
        if value / data[0] < 110:
            continue
        open_position(stock, value)
        if len(context.portfolio.positions) >= len(buy_stocks):
            break

复制
