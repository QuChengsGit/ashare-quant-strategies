def open_position(security, value):
    order = order_target_value_(security, value)
    if order and order.filled > 0:
        return True
    return False

复制
