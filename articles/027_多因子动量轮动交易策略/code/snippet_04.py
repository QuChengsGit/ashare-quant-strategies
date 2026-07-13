def get_value_stock_list(context):
    print("大盘价值成长风格")
    df_stocknum = pd.DataFrame(columns=['过滤后的股票'])
    initial_list = filter_stock(context)
    # 1. 过滤流通市值大于市场中位数的股票
    df1 = get_fundamentals(query(valuation.circulating_cap, balance.total_current_assets, balance.total_current_liability, indicator.inc_return, income.np_parent_company_owners, valuation.code).filter(valuation.code.in_(initial_list)), date=context.previous_date)
    df1['current'] = df1['total_current_assets'] / df1['total_current_liability']
    current_median = df1['current'].median()
    roe_median = df1['inc_return'].median()
    np_parent_company_owners_median = np.median([one for one in df1['np_parent_company_owners'] if one >= 0])
    df1 = df1.sort_values('circulating_cap', ascending=False)
    list_1 = list(df1.code)[:int(0.5 * len(df1.code))]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_1)}, ignore_index=True)
    # 2. 流动比率大于市场中位数的股票
    df2 = get_fundamentals(query(balance.total_current_assets, balance.total_current_liability, valuation.code).filter(valuation.code.in_(list_1)), date=context.previous_date)
    df2['current'] = df2['total_current_assets'] / df2['total_current_liability']
    list_2 = list(df2[df2['current'] > current_median].code)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_2)}, ignore_index=True)
    # 3. ROE大于市场中位数的股票
    df3 = get_fundamentals(query(indicator.inc_return, valuation.code).filter(valuation.code.in_(list_2)), date=context.previous_date)
    list_3 = list(df3[df3['inc_return'] > roe_median].code)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_3)}, ignore_index=True)
    # 4. 近四个季度自由现金流量均为正值
    df4 = get_history_fundamentals(list_3, fields=[indicator.code, cash_flow.net_operate_cash_flow, cash_flow.net_invest_cash_flow, cash_flow.fix_intan_other_asset_acqui_cash], watch_date=context.previous_date, count=4, interval='1q').dropna()
    df4['FCF'] = df4['net_operate_cash_flow'] - df4['fix_intan_other_asset_acqui_cash']
    s_delta_avg = df4.groupby('code')['FCF'].apply(lambda x: x.min() > 0).sort_values(ascending=False)
    list_4 = list(s_delta_avg[s_delta_avg > 0].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_4)}, ignore_index=True)
    # 5. 营业利润增长率大于10%的股票
    df5 = get_history_fundamentals(list_4, fields=[indicator.code, indicator.inc_operation_profit_year_on_year], watch_date=context.previous_date, count=4, interval='1q').dropna()
    s_delta_avg = df5.groupby('code')['inc_operation_profit_year_on_year'].apply(lambda x: x.min() > 10).sort_values(ascending=False)
    list_5 = list(s_delta_avg[s_delta_avg > 0].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_5)}, ignore_index=True)
    # 6. 归母净利润大于行业两倍中位数的股票
    df6 = get_history_fundamentals(list_5, fields=[indicator.code, income.np_parent_company_owners], watch_date=context.previous_date, count=4, interval='1q').dropna()
    s_delta_avg = df6.groupby('code')['np_parent_company_owners'].apply(lambda x: x.min() > 2 * np_parent_company_owners_median).sort_values(ascending=False)
    list_6 = list(s_delta_avg[s_delta_avg > 0].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_6)}, ignore_index=True)
    # 7. 按市净率选取低的股票
    df7 = get_fundamentals(query(valuation.pb_ratio, valuation.code).filter(valuation.code.in_(list_6)), date=context.previous_date)
 df7 = df7.sort_values('pb_ratio', ascending=True)
    list_7 = list(df7[:g.stock_num].code)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_7)}, ignore_index=True)
    print(df_stocknum)
    return list_7[:g.stock_num], len(list_6)
