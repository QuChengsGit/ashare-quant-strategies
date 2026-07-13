def adjustment(context, yesterday):
    """
    调仓逻辑：从全市场选股 -> 基础过滤 -> 高成长筛选 -> 剔除黑名单及涨停 -> 买卖执行
    """
    # 1. 获取昨日可交易的全市场股票列表（排除基金等）
    all_stocks = list(get_all_securities(types=['stock'], date=yesterday).index)
    # 2. 基础过滤：ST、退市风险、新股、停牌等
    candidate_list = basic_filters(context, all_stocks)
    # 3. 财务因子筛选：PEG + 盈利与营收的高增长
    #    多取 5 倍的候选数量，防止部分标的当天涨停买不进去
    high_growth_list = get_high_growth_stocks(context, candidate_list)
    g.buy_list = high_growth_list[:g.total_stock_num * 2]
    # 4. 获取最近 N 日内有涨停的股票（防止短期反复追高）
    recent_limit_up_list = get_recent_limit_up_stock(context, g.buy_list, g.limit_days)
    # 5. 黑名单：最近一段时间内持有且涨停过的股票不再买入
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    # 从买入列表中剔除黑名单股票
    g.buy_list = [stock for stock in g.buy_list if stock not in black_list]
    # 6. 过滤当天已经涨停的股票（涨停价等于 last_price，不再作为买入目标）
    g.buy_list = filter_limitup_stock(context, g.buy_list)
    # 若候选数量大于预设持仓上限，则截取前 N 只
    g.buy_list = g.buy_list[:min(g.total_stock_num, len(g.buy_list))]
    # 7. 卖出不在买入列表且不是昨日涨停股的持仓
    all_positions = context.portfolio.positions
    current_data = get_current_data()  # 减少重复调用
    for stock in all_positions:
        # 若股票既不在新的买入列表中，也不在昨日涨停列表中，则卖出
        if (stock not in g.buy_list) and (stock not in g.high_limit_list):
            limit_price = current_data[stock].last_price * 0.9  # 设置一个略折价的保护限价
            order_target(stock, 0, MarketOrderStyle(limit_price))
            log.info("日常调仓卖出 [%s]" % stock)
        else:
            log.info("日常调仓，继续持有 [%s]" % stock)
    # 8. 资金分配与买入逻辑
    # 计算目标持仓数量与当前持仓数量的差值
    no_hold_target_num = g.total_stock_num - len(context.portfolio.positions)
    # 需要新增仓位时才进行买入
    if no_hold_target_num > 0:
        # 可用资金均分到每一只待买入股票
        cash_per_stock = context.portfolio.available_cash / float(no_hold_target_num)
        for stock in g.buy_list:
            # 仅对当前未持仓的标的进行买入操作
            if stock not in g.hold_list:
                limit_price = current_data[stock].last_price * 1.1  # 向上浮动一定比例做容错
                order_target_value(stock, cash_per_stock, MarketOrderStyle(limit_price))
                log.info("买入目标股票 [%s]，目标市值：%.2f" % (stock, cash_per_stock))
