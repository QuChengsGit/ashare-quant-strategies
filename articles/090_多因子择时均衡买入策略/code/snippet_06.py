def before_trading_start(context):
    initHandleParam()  # 初始化全局变量
    prev_trade_day = context.previous_date  # 获取前一个交易日
    stock_pool = get_all_securities(['stock'], date=prev_trade_day)  # 获取所有股票池
    stock_list = filter_stock(stock_pool)  # 过滤掉不符合条件的股票
    # 获取均线数据
    p1_ma5 = get_stock_price(stock_list, prev_trade_day, 5).groupby('code').mean()
    p1_ma10 = get_stock_price(stock_list, prev_trade_day, 10).groupby('code').mean()
    p1_ma20 = get_stock_price(stock_list, prev_trade_day, 20).groupby('code').mean()
    p1_ma30 = get_stock_price(stock_list, prev_trade_day, 30).groupby('code').mean()
    p2_ma5 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 5).groupby('code').mean()
    p2_ma10 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 10).groupby('code').mean()
    p2_ma20 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 20).groupby('code').mean()
    p2_ma30 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 30).groupby('code').mean()
    # 均线与量价指标的多因子筛选
    dx1 = []
    for stock in stock_list:
        if p1_ma5['close'][stock] < p1_ma10['close'][stock] \
                and p2_ma5['close'][stock] > p2_ma10['close'][stock] \
                and p2_ma5['volume'][stock] > p2_ma10['volume'][stock] \
                and (p1_ma5['volume'][stock] * 1.2) > p1_ma10['volume'][stock] \
                and p1_ma20['close'][stock] > p2_ma20['close'][stock] \
                and p1_ma30['close'][stock] > p2_ma30['close'][stock]:
            dx1.append(stock)
    print('dx1可选股票%s支.' % (len(dx1)))
    # MACD信号筛选
    dx2 = []
    macd_dif, macd_dea, macd_macd = MACD(security_list=dx1, check_date=prev_trade_day, SHORT=12, LONG=26, MID=9, unit='1d')
    for stock in dx1:
        if macd_dif[stock] > 0 and macd_dea[stock] > 0 and 0 > macd_dea[stock] - macd_dif[stock] > -0.1:
            dx2.append(stock)
    print('dx2可选股票%s支' % (len(dx2)))
    # 资金流向筛选
    dx3 = []
    for stock in dx2:
        p1_flow = get_money_flow(security_list=stock, end_date=prev_trade_day, count=1, fields=['change_pct'])
        p2_flow = get_money_flow(security_list=stock, end_date=getday3(prev_trade_day, -1), count=1, fields=['change_pct'])
        if len(p1_flow['change_pct']) == 0 or len(p2_flow['change_pct']) == 0:
            continue
        if (p1_flow['change_pct'][0] > 0 and p2_flow['change_pct'][0] < 0) \
                or (p1_flow['change_pct'][0] < 0 and p2_flow['change_pct'][0] > 0):
            dx3.append(stock)
    print('dx3可选股票%s支' % (len(dx3)))
    # 最终筛选出满足条件的股票列表
    dx5 = []
    current_data = get_current_data()
    for stock in dx3:
        p1_1 = get_price(security=stock, end_date=prev_trade_day, frequency='1d', fields=['close'],
                         panel=False, count=1, skip_paused=True)
        if p1_1['close'][0] <= current_data[stock].day_open:
            continue
        dx5.append(stock)
    print('dx5可选股票%s支' % (len(dx5)))
    g.buy_list = dx5
    g.buy_list.sort()
    print('%s:共找到%d只股票可以购买.%s' % (context.current_dt, len(g.buy_list), g.buy_list))

复制
