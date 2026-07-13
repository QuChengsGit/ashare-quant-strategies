def close_account(context):
    if g.no_trading_today_signal and g.hold_list:
        for stock in g.hold_list:
            order_target_value(stock, 0)
            log.info("卖出[%s]" % stock)

复制
