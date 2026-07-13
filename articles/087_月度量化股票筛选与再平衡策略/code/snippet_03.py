def before_market_open(context):
    # 获得当前日期
    rebalance_day = context.current_dt.date()
    next_day = shift_trading_day(rebalance_day, 1)
    if next_day.month != rebalance_day.month:
        if next_day.day < rebalance_day.day:
            log.info(f'############## trade day：{str(rebalance_day)} ##############')
            g.if_trade = True
