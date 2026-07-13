def get_stock_list(context):
    curr_data = get_current_data()
    yesterday = context.previous_date
    df_stocknum = pd.DataFrame(columns=['当前符合条件股票数量'])
    by_date = yesterday - datetime.timedelta(days=1200)  # 三年
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 0. 过滤创业板、科创板、ST股等
    initial_list = [stock for stock in initial_list if not (
            curr_data[stock].day_open == curr_data[stock].high_limit or
            curr_data[stock].day_open == curr_data[stock].low_limit or
            curr_data[stock].paused
    )]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(initial_list)}, ignore_index=True)
    # 1. 资产负债率由高到低后70%
    df = get_fundamentals(query(
        balance.code, balance.total_liability, balance.total_assets
    ).filter(
        valuation.code.in_(initial_list)
    )).dropna()
    df['ratio'] = df['total_liability'] / df['total_assets']
    df = df.sort_values(by='ratio', ascending=False)
    low_liability_list = list(df.code)[int(0.3*len(list(df.code))):]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(low_liability_list)}, ignore_index=True)
    # 2. 选出不良资产比率在总体中[20%-80%]范围内的股票
    df1 = get_fundamentals(query(
        balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
        balance.other_receivable, balance.good_will, balance.intangible_assets,
        balance.inventories, balance.constru_in_process
    ).filter(
        balance.code.in_(low_liability_list)
    )).dropna()
    df1['bad_assets'] = df1.sum(axis=1) - df1['total_assets']
    df1['ratio1'] = df1['bad_assets'] / df1['total_assets']
    df1 = df1.sort_values(by='ratio1', ascending=False)
    proper_receivable_list = list(df1.code)[int(0.1*len(list(df1.code))):int(0.9*len(list(df1.code)))]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(proper_receivable_list)}, ignore_index=True)
    # 3. 优质资产周转率前75%的公司
    df2 = get_fundamentals(query(
        balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
        balance.other_receivable, balance.good_will, balance.intangible_assets,
        balance.inventories, balance.constru_in_process, income.total_operating_revenue
    ).filter(
        balance.code.in_(proper_receivable_list)
    )).dropna()
    df2['good_assets'] = df2['total_assets'] - (df2.sum(axis=1) - df2['total_assets'] - df2['total_operating_revenue'])
    df2['ratio2'] = df2['total_operating_revenue'] / df2['good_assets']
    df2 = df2.sort_values(by='ratio2', ascending=False)
    proper_receivable_list1 = list(df2.code)[:int(0.75*len(list(df2.code)))]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(proper_receivable_list1)}, ignore_index=True)
    # 4. 过去四个季度ROA增长最多(前20%)的股票
    df3 = get_history_fundamentals(
        proper_receivable_list1,
        fields=[indicator.code, indicator.roa],
        watch_date=yesterday,
        count=4,
        interval='1q'
    ).dropna()
    s_delta_avg = df3.groupby('code')['roa'].apply(
        lambda x: x.iloc[3] - x.mean() if len(x) == 4 else 0.0
    ).sort_values(ascending=False)
    roa_list = list(s_delta_avg[:int(0.2 * len(s_delta_avg))].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(roa_list)}, ignore_index=True)
    # 5. 最终筛选股票
    pb_list = get_fundamentals(query(
        valuation.code
    ).filter(
        valuation.code.in_(roa_list),
        valuation.pb_ratio > 0.7,
        valuation.ps_ratio < 3
    ).order_by(
        valuation.pb_ratio.asc()
    ))['code'].tolist()
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(pb_list)}, ignore_index=True)
    print(df_stocknum)
    final_list = pb_list[:g.stock_num]
    return final_list
