def order_target_value_(security, value):
    if value == 0:
        log.debug(f"Selling out {security}")
    else:
        log.debug(f"Order {security} to value {value}")
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    if order is not None and order.filled > 0:
        return True
    return False
def close_position(position):
    order = order_target_value_(position.security, 0)
    if order is not None and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False

复制
