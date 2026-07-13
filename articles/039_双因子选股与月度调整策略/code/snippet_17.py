# 自定义下单函数
def order_target_value_(security, value):
    if value == 0:
        log.debug(f"Selling out {security}")
    else:
        log.debug(f"Order {security} to value {value:.2f}")
    return order_target_value(security, value)
# 开仓函数
def open_position(security, value):
    _order = order_target_value_(security, value)
    if _order is not None and _order.filled > 0:
        return True
    return False
# 平仓
函数
def close_position(position):
    security = position.security
    _order = order_target_value_(security, 0)
    if _order is not None:
        if _order.status == OrderStatus.held and _order.filled == _order.amount:
            return True
    return False
