def before_market_open(context):
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    # 获取所有可交易的股票列表
    initial_list = get_all_securities().index.tolist()
    # 过滤股票
    initial_list = filter_trade_stock(context, initial_list)
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_paused_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 根据动量筛选股票
    next_holding_codes = get_momentum(context, initial_list)
    # 获取当前持仓的股票代码
    holding_codes = list(context.portfolio.positions.keys())
    # 昨日持仓但今日不再持有的股票
    g.security1 = [x for x in holding_codes if x not in next_holding_codes]
    # 今日新增持仓的股票
    g.security2 = [y for y in next_holding_codes if y not in holding_codes]
