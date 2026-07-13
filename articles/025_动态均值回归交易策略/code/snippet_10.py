def weekly(context):
    g.sel_stock = None
    current_data = get_current_data()
    stock_list = get_all_securities().index.tolist()
    # 获取最近5天的收盘价并计算均值
    last_5_prices = history(count=5, field='close', security_list=stock_list)
    last_5_prices = pd.DataFrame({'mean_val': last_5_prices.mean()})
    # 均值升序排序
    last_5_prices_sort = last_5_prices.sort_values(by='mean_val', ascending=True)
    # 选择均值大于等于1.5的股票
    last_5_prices_stock = last_5_prices_sort.query('mean_val >= 1.5').index.tolist()
    # 去除停牌、ST股以及带有退市风险的股票
    for security in last_5_prices_stock:
        if not current_data[security].paused and not current_data[security].is_st and '*' not in current_data[security].name and '退' not in current_data[security].name:
            g.sel_stock = security
            break
    if g.sel_stock is not None:
        log.info(f"选定股票: {g.sel_stock} - {get_security_info(g.sel_stock).display_name}")
        # 卖出不在持仓列表的股票
        sell_list = set(context.portfolio.positions.keys()) - set([g.sel_stock])
        for stock in sell_list:
            order_target_value(stock, 0)
    else:
        for stock in context.portfolio.positions.keys():
            order_target_value(stock, 0)

复制
