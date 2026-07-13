def before_market_open(context):
    g.pre_holdings = list(context.portfolio.positions)  # 已持仓股票
    # 过滤次新股
    by_date = context.previous_date - timedelta(days=30)
    stock_list = list(get_all_securities(['stock'], date=by_date).index)
    # 过滤ST、停牌，创业板、科创板股票
    current_data = get_current_data()
    stock_list = [code for code in stock_list if not (
            code.startswith(('3', '68', '4', '8'))
            or current_data[code].is_st
            or current_data[code].paused
    )]
    # 过滤市值过大的股票
    stock_list = get_fundamentals(
        query(
            valuation.code
        ).filter(
            valuation.code.in_(stock_list),
            valuation.circulating_market_cap < 150
        )
    )['code'].tolist()
    # 选出可能涨停的股票
    g.help_stock = pick_high_limit(context, stock_list)
def pick_high_limit(context, stocks):
    end_date = context.previous_date
    df_pre = get_price(stocks, end_date=end_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False
                       ).query('close < high_limit').set_index('code')
    s_pre_close = df_pre['close']
    stock_list = df_pre.index.tolist()
    df_day_300 = get_price(stock_list, end_date=end_date, frequency='daily',
                           fields=['close'], count=300, panel=False)
    s_high_300 = df_day_300.groupby('code')['close'].apply(lambda x: x.max())
    s_rate_300 = df_day_300.groupby('code')['close'].apply(lambda x: x.max() / x.min() - 1)
    s_high_50 = df_day_300.groupby('code')['close'].apply(lambda x: x[-50:].max())
    s_high_10 = df_day_300.groupby('code')['close'].apply(lambda x: x[-10:].max())
    s_rate_10 = df_day_300.groupby('code')['close'].apply(lambda x: x[-10:].max() / x[-10:].min() - 1)
    target_list = pd.DataFrame(
        {'pre_close': s_pre_close, 'high_300': s_high_300, 'rate_300': s_rate_300,
         'high_50': s_high_50, 'high_10': s_high_10, 'rate_10': s_rate_10
         }
    ).dropna().query(
        'pre_close * 1.2 > high_300 and pre_close * 1.2 > high_50 and pre_close * 1.1 > high_10 and '
        'rate_300 < 2 and rate_10 <= 0.5'
    ).index.tolist()
    dict_high_limit = get_price(target_list, end_date=context.current_dt, fields=['high_limit'],
                                count=1, panel=False).set_index('code')['high_limit'].to_dict()
    return dict_high_limit
