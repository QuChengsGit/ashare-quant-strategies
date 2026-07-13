def get_signal(context):
    g.df_etf = pd.DataFrame(columns=['基金代码', '基金名称','涨幅','均线状态','股数'])
    total_value = context.portfolio.total_value
    current_time = context.current_dt
    for mkt_idx in g.ETFList:
        security = g.ETFList[mkt_idx]
        etf_name = get_security_info(security).display_name
        price_data = get_price(security, end_date=current_time, frequency='1d', fields=['close'], count=g.moment_period+1)
        now_close = price_data['close'][-1]
        previous_close = price_data['close'][-g.moment_period]
        ma_filter = ta.MA(price_data.close.values, g.ma_period)[-1]
        ma_status = now_close - ma_filter
        moment = (now_close - previous_close) / previous_close * 100
        amount = int(total_value / now_close / g.type_num /100)*100
        g.df_etf = g.df_etf.append({'基金代码': security, 
                                    '基金名称': etf_name,
                                    '涨幅': moment,
                                    '均线状态': ma_status,
                                    '股数': amount},
                                   ignore_index=True)
    g.df_etf.sort_values(by='涨幅', axis=0, ascending=False, inplace=True)
    tb = pt.PrettyTable()
    tb.add_column('ETF Code', list(g.df_etf['基金代码']))
    tb.add_column('Name', list(g.df_etf['基金名称']))
    tb.add_column('Moment', list(g.df_etf['涨幅'].values.round(2)))
    tb.add_column('Ma_Status', list(g.df_etf['均线状态'].values.round(2)))
    tb.add_column('Amount', list(g.df_etf['股数']))
    log.info('\n行情统计: \n%s' % tb)
    # 筛选符合条件的标的
    g.df_etf_buy = g.df_etf[(g.df_etf['涨幅'] > 0) & (g.df_etf['均线状态'] > 0)]
    # 根据不同资产类别进行分类
    g.df_local_stocks = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.local_stocks)]
    g.df_global_stocks = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.global_stocks)]
    g.df_local_futures = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.local_futures)]
    g.df_global_futures = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.global_futures)]
    g.df_reits = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.REITs)]
    g.holdings = set(context.portfolio.positions.keys())
    g.targets = []
    if len(g.df_local_stocks) > 0:
        g.targets.append(g.df_local_stocks.iloc[0]['基金代码'])
    if len(g.df_global_stocks) > 0:
        g.targets.append(g.df_global_stocks.iloc[0]['基金代码'])
    if len(g.df_local_futures) > 0:
        g.targets.append(g.df_local_futures.iloc[0]['基金代码'])
    if len(g.df_global_futures) > 0:
        g.targets.append(g.df_global_futures.iloc[0]['基金代码'])
    if len(g.df_reits) > 0:
        g.targets.append(g.df_reits.iloc[0]['基金代码'])
    g.sells = [i for i in g.holdings if i not in g.targets]
    g.purchases = [i for
 i in g.targets if i not in g.holdings]
    # 输出交易计划
    content = '交易计划：\n'
    if len(g.sells) > 0:
        tb = pt.PrettyTable()
        df_sells = g.df_etf.loc[g.df_etf['基金代码'].isin(g.sells)]
        tb.add_column('ETF Code', list(df_sells['基金代码']))
        tb.add_column('Name', list(df_sells['基金名称']))
        str_more = '\n计划卖出: \n' + str(tb)
        content += str_more
        log.info(str_more)
    if len(g.purchases) > 0:
        tb = pt.PrettyTable()
        df_purchase = g.df_etf.loc[g.df_etf['基金代码'].isin(g.purchases)]
        tb.add_column('ETF Code', list(df_purchase['基金代码']))
        tb.add_column('Name', list(df_purchase['基金名称']))
        tb.add_column('Amount', list(df_purchase['股数']))
        str_more = '\n计划买入：\n' + str(tb)
        content += str_more
        log.info(str_more)
    if (len(g.sells) == 0) and (len(g.purchases) == 0):
        log.info('\n无交易计划: \n')
    return
