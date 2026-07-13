def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    today_date = context.current_dt.date()
    lastd_date = context.previous_date
    befor_date = get_trade_days(end_date=today_date, count=3)[0]
    all_data = get_current_data()
    g.poolist = []
    g.sell_list = []
    # 基准指数票池筛选
    if g.index == 'all':
        stocklist = list(get_all_securities(['stock']).index)
    elif g.index == 'zz':
        stocklist = get_index_stocks('000300.XSHG', date=None) + get_index_stocks('000905.XSHG', date=None) + get_index_stocks('000852.XSHG', date=None)
    else:
        stocklist = get_index_stocks(g.index, date=None)
    stocklist = [stockcode for stockcode in stocklist if not all_data[stockcode].paused]
    stocklist = [stockcode for stockcode in stocklist if not all_data[stockcode].is_st]
    stocklist = [stockcode for stockcode in stocklist if '退' not in all_data[stockcode].name]
    stocklist = [stockcode for stockcode in stocklist if stockcode[0:3] != '688']
    stocklist = [stockcode for stockcode in stocklist if (today_date - get_security_info(stockcode).start_date).days > 365]
    poollist = get_up_filter_jiang(context, stocklist, lastd_date, 1, 1, 0)
    list_201 = get_up_filter_jiang(context, poollist, lastd_date, 20, 1, 0)
    g.poollist = optimize_filter(context, list_201, 'L')
    # 增加天量/爆量过滤
    if g.volume_control != 0:
        g.poollist = get_highvolume_filter(context, g.poollist, g.volume_control, g.volume_period, g.volume_ratio)
    # 增加持仓股的量能卖出控制
    if g.sell_mode != 0 and len(context.portfolio.positions) != 0:
        stocklist = list(context.portfolio.positions)
        g.sell_list = get_highvolume_filter(context, stocklist, g.sell_mode, g.sell_vol_period, g.sell_vol_ratio)

复制
