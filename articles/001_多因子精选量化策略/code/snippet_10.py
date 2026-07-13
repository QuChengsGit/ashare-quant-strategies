def prepare_stock_list(context):
    # 获取当前持仓股票列表
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    # 获取昨日涨停的股票
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.yesterday_HL_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.yesterday_HL_list = []
    # 判断今天是否为资金再平衡日
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')

复制
