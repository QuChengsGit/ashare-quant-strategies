def order_target_value_(security, value):
    if value == 0:
        log.debug("卖出 %s" % (get_name(security)))
    else:
        log.debug("买入 %s ，市值： %f" % (get_name(security), value))
    return order_target_value(security, value)
