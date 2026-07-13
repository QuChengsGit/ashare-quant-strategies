def prepare_stock_list(context):
    # 获取持仓中昨日涨停的股票
    g.high_limit_list = []
    hold_list = list(context.portfolio.positions)
    if hold_list:
        df = get_price(hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close == high_limit and paused == 0')['code'].tolist()

复制
