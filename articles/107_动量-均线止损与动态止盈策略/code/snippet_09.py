def order_target_value_(security, value):
    if value == 0:
        log.debug("卖出 %s" % (security))
    else:
        log.debug("调整 %s 市值到 %f" % (security, value))
    return order_target_value(security, value)
