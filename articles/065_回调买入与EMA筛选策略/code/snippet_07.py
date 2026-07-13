def my_trade(context):
    sell(context)
    buy(context)
def sell(context):
    # 卖出持仓中的所有股票
    for position in list(context.portfolio.positions.values()):
        if position.closeable_amount > 0:
            close_position(position)
def buy(context):
    data_today = get_current_data()
    position_count = len(context.portfolio.positions)
    # 选股逻辑：昨日收盘价大于5日均价，且今日开盘价低于昨日最低价
    buy_stocks = []
    for s in g.stock_pool:
        if position_count + len(buy_stocks) >= g.stock_num:
            break
        df = attribute_history(s, 5, '1d', ('close', 'low', 'high', 'paused'), False)
        if df['paused'].max() == 0:  # 过去5天没有停盘
            today_open = data_today[s].day_open
            prev_close = df['close'][-1]
            prev_low = df['low'][-1]
            chg = (today_open - prev_close) / prev_close * 100  # 计算开盘时跌幅
            if today_open < prev_low and -8 < chg < -1:
                low = min(df['low'].values[-4:])
                high = max(df['high'].values[-4:])
                precent = (high - low) / low * 100  # 计算4天振幅
                if precent <= 20:
                    df['ema'] = df['close'].ewm(span=5).mean()
                    ema = df['ema'].values[-1]
                    if prev_close > ema:
                        buy_stocks.append(s)
    # 按选股数分配资金买入
    target_num = len(buy_stocks)
    if target_num > 0:
        value = context.portfolio.available_cash / g.stock_num
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                open_position(stock, value)

复制
