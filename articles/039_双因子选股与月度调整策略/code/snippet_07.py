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
