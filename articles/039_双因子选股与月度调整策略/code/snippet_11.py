def prepare_stock_list(context):
    g.hold_list = list(context.portfolio.positions)  # 更新持仓列表
    # 获取持仓的昨日涨停股票列表
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close == high_limit and paused == 0')['code'].tolist()

复制
