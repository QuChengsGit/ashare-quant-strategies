def daily_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    base = get_bars('000852.XSHG', 30, unit='1d',
                    fields=['date', 'open', 'close', 'high', 'low', 'volume', 'money'],
                    include_now=False, end_dt=None, df=True)
    base['EMA2'] = talib.EMA(base['close'], 2)
    base['EMA4'] = talib.EMA(base['close'], 4)
    base['dif'] = base['EMA2'] - base['EMA4']
    base['dea'] = talib.EMA(base['dif'], 4)
    base['signal'] = np.where(base['dif'] - base['dea'] < 0, 1, 0)
    today_sig = np.array(base['signal'])[-1]
    if today_sig > 0:
        for stock in g.hold_list:
            position = context.portfolio.positions[stock]
            close_position(position)
            log.info(f"风控触发，平仓卖出{stock}")
        return
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info(f"卖出[{stock}]")
            position = context.portfolio.positions[stock]
            close_position(position)
    position_count = len(context.portfolio.positions)
    target_num = len(target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == target_num:
                        break

复制
