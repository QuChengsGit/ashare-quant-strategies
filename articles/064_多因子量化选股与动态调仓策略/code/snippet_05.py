def before_market_open(context):
    g.hold_list = list(context.portfolio.positions)
    if g.hold_list:
        yesterday = datetime.datetime.strftime(context.previous_date, '%Y-%m-%d')
        df = get_price(g.hold_list, end_date=yesterday, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.high_limit_list = []
    today = datetime.datetime.strftime(context.current_dt, '%Y-%m-%d')
    pre_m = datetime.datetime.strftime(context.previous_date, '%m')
    cur_m = datetime.datetime.strftime(context.current_dt, '%m')
    if cur_m != pre_m:
        g.signal = True
        stock_list = select_stocks(context)
        curr_stock_list = get_index_stocks('000002.XSHG', today) + get_index_stocks('399107.XSHE', today)
        curr_stock_list = list(set(curr_stock_list))
        g.alllist = [stk for stk in stock_list if stk in curr_stock_list]
    else:
        g.signal = False
        g.alllist = []
def select_stocks(context):
    # 构造训练集并训练模型
    date_list = get_period_date('M', start_date, yesterday)
    for date in date_list:
        if date not in g.factor_cache:
            factor_data = get_factor_data(stock_list, date)
            industry_code = list(get_industries('sw_l1', date).index)
            g.factor_cache[date] = data_preprocessing(factor_data, stock_list, industry_code, date)
    train_data = pd.concat([g.factor_cache[date] for date in date_list[:-1]], axis=0)
    train_target = train_data.pop('label')
    clf = g.regressor(**g.params)
    clf.fit(train_data.values, train_target.values)
    # 测试集选股
    test_data = g.factor_cache[date_list[-1]]
    prob = clf.predict_proba(test_data.values)[:, 1]
    df = pd.DataFrame(index=test_data.index)
    df['score'] = prob
    df = df.sort_values(by='score', ascending=False)
    stocks = df.head(int(0.1 * df.shape[0])).index.tolist()
    return stocks

复制
