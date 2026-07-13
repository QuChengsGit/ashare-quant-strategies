def close_position(position):
    security = position.security
    _order = order_target_value_(security, 0)
    if _order is not None:
        if _order.status == OrderStatus.held and _order.filled == _order.amount:
            return True
    return False
