def get_stock_list(context):
    curr_data = get_current_data()  # 获取当前行情数据
    yesterday = context.previous_date  # 获取前一个交易日的日期
    # 初步筛选符合条件的股票列表
    by_date = yesterday - datetime.timedelta(days=1200)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 过滤次新股、ST、停牌、涨跌停股票
    initial_list = [stock for stock in initial_list if not (
        (curr_data[stock].day_open == curr_data[stock].high_limit) or
        (curr_data[stock].day_open == curr_data[stock].low_limit) or
        curr_data[stock].paused or
        ('ST' in curr_data[stock].name) or
        ('*' in curr_data[stock].name) or
        ('退' in curr_data[stock].name)
    )]
    # 筛选资产负债率较低的股票
    df = get_fundamentals(query(
            balance.code, balance.total_liability, balance.total_assets
        ).filter(
            valuation.code.in_(initial_list)
        )
    ).dropna()
    df['ratio'] = df['total_liability'] / df['total_assets']
    df = df.sort_values(by='ratio', ascending=False)
    low_liability_list = list(df.code)[int(0.3*len(df.code)):]
    # 筛选不良资产率适中的股票
    df1 = get_fundamentals(query(
            balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
            balance.other_receivable, balance.good_will, balance.intangible_assets,
            balance.inventories, balance.constru_in_process
        ).filter(
            balance.code.in_(low_liability_list)
        )
    ).dropna()
    df1['bad_assets'] = df1.sum(axis=1) - df1['total_assets']
    df1['ratio1'] = df1['bad_assets'] / df1['total_assets']
    df1 = df1.sort_values(by='ratio1', ascending=False)
    proper_receivable_list = list(df1.code)[int(0.1*len(df1.code)):int(0.9*len(df1.code))]
    # 筛选优质资产周转率较高的股票
    df2 = get_fundamentals(query(
            balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
            balance.other_receivable, balance.good_will, balance.intangible_assets,
            balance.inventories, balance.constru_in_process, income.total_operating_revenue
        ).filter(
            balance.code.in_(proper_receivable_list)
        )
    ).dropna()
    df2['good_assets'] = df2['total_assets'] - (df2.sum(axis=1) - df2['total_assets'] - df2['total_operating_revenue'])
    df2['ratio2'] = df2['total_operating_revenue'] / df2['good_assets']
    df2 = df2.sort_values(by='ratio2', ascending=False)
    proper_receivable_list1 = list(df2.code)[:int(0.75*len(df2.code))]
    # 筛选ROA增长显著的股票
    df3 = get_history_fundamentals(
        proper_receivable_list1, fields=[indicator.code, indicator.roa],
        watch_date=yesterday, count=4, interval='1q'
    ).dropna()
    s_delta_avg = df3.groupby('code')['roa'].apply(
        lambda x: x.iloc[3] - x.mean() if len(x) == 4 else 0.0
    ).sort_values(ascending=False)
    roa_list = list(s_delta_avg[:int(0.2*len(s_delta_avg))].index)
    # 筛选市净率较低的股票并生成最终买入列表
    pb_list = get_fundamentals(query(
        valuation.code
    ).filter(
        valuation.code.in_(roa_list),
        valuation.pb_ratio > 0.7,
        valuation.ps_ratio < 3
    ).order_by(
        valuation.pb_ratio.asc()
    ))['code'].tolist()
    final_list = pb_list[:g.stock_num]
    return final_list

复制
