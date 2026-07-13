def weekly_adjustment(context):
    # 获取应买入股票列表
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)  # 过滤停牌股票
    target_list = filter_limitup_stock(context, target_list)  # 过滤涨停股票
    target_list = filter_limitdown_stock(context, target_list)  # 过滤跌停股票
    # 截取最大持仓数量的股票
    target_list = target_list[:min(g.stock_num, len(target_list))]
    # 卖出不再持有的股票
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.yesterday_HL_list):
            log.info("卖出[%s]" % (stock))  # 卖出股票日志
            position = context.portfolio.positions[stock]
            close_position(position)  # 平仓
        else:
            log.info("已持有[%s]" % (stock))  # 股票仍持有
    # 买入新的股票
    position_count = len(context.portfolio.positions)
    target_num = len(target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)  # 根据现金分配买入股票
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):  # 开仓
                    if len(context.portfolio.positions) == target_num:
                        break

复制
