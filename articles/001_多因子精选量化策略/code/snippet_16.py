def order_target_value_(security, value):
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order and order.filled > 0
def close_position(position):
    return order_target_value_(position.security, 0)

复制
