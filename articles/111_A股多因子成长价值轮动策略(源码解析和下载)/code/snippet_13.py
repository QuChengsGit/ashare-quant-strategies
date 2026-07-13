def order_target_value_(security, value):
    if value == 0: log.debug("Selling out %s" % security)
    else: log.debug("Order %s to value %f" % (security, value))
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    return order is not None
