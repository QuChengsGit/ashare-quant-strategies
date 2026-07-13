def open_position(security, value):
    order = order_target_value(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    security = position.security
    order = order_target_value(security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
def adjust_position(context, buy_stocks, stock_num):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
    if stock_num > len(context.portfolio.positions):
        value = context.portfolio.cash / (stock_num - len(context.portfolio.positions))
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        break
