def buy(context):
    data_today = get_current_data()
    available_slots = g.amount - len(context.portfolio.positions)
    if available_slots <= 0:
        print("no position")
        return
    allocation = context.portfolio.cash / available_slots
    for s in g.muster:
        if len(context.portfolio.positions) == g.amount:
            break
        if (history(5, '1d', 'paused', s).max().values[0] == 0):
            low = history(4, '1d', 'low', s).min().values[0]
            high = history(4, '1d', 'high', s).max().values[0]
            percent = (high - low) / low * 100
            if percent <= 10:
                open_price_today = data_today[s].day_open
                prev_close = get_price(s, count=1, end_date=context.previous_date).iloc[-1]['close']
                his = history(60, '1d', 'close', s)
                ema = talib.EMA(his.values.flatten(), timeperiod=5)[-1]
                if prev_close > ema:
                    if get_price(s, count=1, end_date=context.previous_date).iloc[-1]['low'] > open_price_today:
                        order(s, int(allocation / open_price_today))

复制
