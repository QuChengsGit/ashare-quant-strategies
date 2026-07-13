def period(context):
    # 获取基本面数据：净利润同比增长率、ROE、市净率、市盈率、市值
    df = get_fundamentals(g.q)[['code', 'inc_net_profit_year_on_year', 'roe', 'pb_ratio', 'pe_ratio', 'market_cap']]
    # 筛选ROE大于4%的股票
    df = df[df['roe'] > 4]
    # 按照市净率排序，取前100只股票
    df = df.sort_values('pb_ratio').head(100)
    df['pbrank'] = df['pb_ratio'].rank()
    # 再按照净利润同比增长率排序，取后50只股票
    df = df.sort_values('inc_net_profit_year_on_year').tail(50)
    df['profitrank'] = df['inc_net_profit_year_on_year'].rank()
    # 最终选定的股票代码
    to_hold = df['code'].values
    # 获取这些股票过去100个交易日的收盘价数据，每20天为一个间隔
    dff = history(count=100*20, unit='1d', field='close', security_list=to_hold)
    dfff = dff.T
    dfff_close = dfff.iloc[:, -1:]
    dfff = dfff.iloc[:, ::20]
    # 处理最近一次的数据，避免重复计算
    dfff_jc = dfff.iloc[:, -1:]
    dfff = dfff.iloc[:, :-1]
    dfff_jc2 = pd.concat([dfff_jc, dfff_close], axis=1, ignore_index=True)
    dfff_jc2.columns = ['jc', 'close']
    dfff_jc2 = dfff_jc2.T.drop_duplicates().T
    dfff = pd.concat([dfff, dfff_jc2], axis=1, ignore_index=True)
    # 计算2000日均线和20日均线
    mal = dfff.mean(axis=1)
    mas = dfff.iloc[:, -20:].mean(axis=1)
    maa = pd.DataFrame({'mas': mas, 'mal': mal})
    maa['mac'] = maa['mas'] - maa['mal']
    # 筛选20日均线低于2000日均线的股票
    buy = maa[maa['mac'] < 0]
    buy['code'] = buy.index
    buy = buy['code'].values
    # 卖出不符合条件的持仓股票
    for stock in context.portfolio.positions:
        if stock not in buy:
            order_target_value(stock, 0)
    # 买入新的符合条件的股票
    to_buy = [stock for stock in buy if stock not in context.portfolio.positions]
    if to_buy:
        cash_per_stock = context.portfolio.available_cash / len(to_buy)
        for stock in to_buy:
            order_value(stock, cash_per_stock)
    log.info(f"现在持有股票数量：{len(context.portfolio.positions)}")

复制
