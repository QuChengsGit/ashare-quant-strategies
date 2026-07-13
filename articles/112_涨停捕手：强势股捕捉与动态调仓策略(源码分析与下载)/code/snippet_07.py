def prepare_stock_list(context):
    # 清空当前持仓股票列表
    g.hold_list = []
    # 获取当前持仓的股票
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    # 获取昨日涨停的股票
    if g.hold_list != []:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]  # 筛选出收盘价等于涨停价的股票
        g.yesterday_HL_list = list(df.code)  # 更新昨日涨停股票列表
    else:
        g.yesterday_HL_list = []
    # 判断是否为账户资金再平衡的日期
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')

复制
