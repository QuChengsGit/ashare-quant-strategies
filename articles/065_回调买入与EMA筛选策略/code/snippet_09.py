# 交易模块-自定义下单
def order_target_value_(security, value):
    if value == 0:
        log.debug("Selling out %s" % security)
    else:
        log.debug("Order %s to value %f" % (security, value))
    return order_target_value(security, value)
# 交易模块-开仓
def open_position(security, value):
    print("buy:" + security + " " + str(value))
    _order = order_target_value_(security, value)
    if _order is not None and _order.filled > 0:
        return True
    return False
# 交易模块-平仓
def close_position(position):
    security = position.security
    _order = order_target_value_(security, 0)
    if _order is not None:
        if _order.status == OrderStatus.held and _order.filled == _order.amount:
            return True
    return False
