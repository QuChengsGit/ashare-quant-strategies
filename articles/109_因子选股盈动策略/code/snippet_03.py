def prepare_stock_list(context):
    # 获取当前持仓列表
    g.hold_list = []
    for position in list(context.portfolio.positions.values()):
        stock = position.security  # 获取持仓股票
        g.hold_list.append(stock)  # 添加到持仓列表
    # 获取昨日涨停的股票列表
    if g.hold_list != []:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]  # 选出涨停的股票
        g.yesterday_HL_list = list(df.code)  # 将涨停股票的代码添加到昨日涨停列表
    else:
        g.yesterday_HL_list = []  # 如果没有持仓，清空涨停股票列表
