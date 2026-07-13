def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
            g.hold_stock = 'null'
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        g.hold_stock = stock
                        break
def open_position(security, value):
    order = order_target_value(security, value)
    if order is not None and order.filled > 0:
        return True
    return False
def close_position(position):
    security = position.security
    order = order_target_value(security, 0)
    if order is not None and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False
