def before_market_open(context):
    yesterday = context.previous_date
    # 获取持仓股票列表和昨日涨停的股票列表
    g.hold_list = [s for s in context.portfolio.positions]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=yesterday, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.yesterday_HL_list = list(df.code)
    else:
        g.yesterday_HL_list = []
    # 获取股票池，按市值排序
    fundamentals_data = get_fundamentals(query(valuation.code, valuation.market_cap).order_by(valuation.market_cap.asc()).filter(valuation.market_cap < 160).limit(g.choice))
    stocks = list(fundamentals_data['code'])
    # 各种过滤条件
    current_data = get_current_data()
    stocks = [s for s in stocks if not current_data[s].paused
              and not current_data[s].is_st
              and 'N' not in current_data[s].name
              and '退' not in current_data[s].name
              and current_data[s].low_limit < current_data[s].day_open < current_data[s].high_limit
              and s[0] != '4' and s[0] != '8' and s[:2] != '68'
              and s not in g.hold_list]
    # 过滤上市时间小于250天的股票
    g.stocks = [stock for stock in stocks if yesterday - get_security_info(stock).start_date > datetime.timedelta(days=250)]
    log.info('股票数量{}'.format(len(g.stocks)))

复制
