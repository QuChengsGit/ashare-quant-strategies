def get_high_limit(context):
    g.high_limit_list = []
    hold_list = list(context.portfolio.positions)
    if hold_list:
        df = get_price(hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1).iloc[:, 0, :]
        g.high_limit_list = list(df[df['close'] == df['high_limit']].index)

复制
