def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in target_list if stock not in black_list]
    target_list = target_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持有[%s]" % (stock))
    position_count = len(context.portfolio.positions)
    if len(target_list) > position_count:
        value = context.portfolio.cash / (len(target_list) - position_count)
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == len(target_list):
                        break
def open_position(security, value):
    order = order_target_value_(security, value)
    if order and order.filled > 0:
        return True
    return False
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    if order and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False
