def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
# 平仓操作
def close_position(position):
    order = order_target_value_(position.security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
