def close_position(position):
    order = order_target_value_(position.security, 0)
    return order and order.status == OrderStatus.held and order.filled == order.amount

复制
