def prepare_stock_list(context):
    """
    准备股票列表，获取当前持仓和昨日涨停股票
    """
    g.hold_list = [position.security for position in context.portfolio.positions.values()]  # 获取当前持仓列表
    if g.hold_list:
        # 获取昨日涨停股票
        df = get_price(g.hold_list,
                       end_date=context.previous_date,
                       frequency='daily',
                       fields=['close', 'high_limit'],
                       count=1,
                       panel=False,
                       fill_paused=False)
        df = df[df['close'] == df['high_limit']]  # 筛选出涨停的股票
        g.yesterday_HL_list = list(df.code)
    else:
        g.yesterday_HL_list = []


g.hold_list：获取当前持仓股票列表，便于在后续处理中排除已经持有的股票。

get_price()：获取持仓股票的昨日收盘价和涨停价。利用这些数据来判断是否需要卖出涨停股票。只有在涨停的股票才会加入 g.yesterday_HL_list。
