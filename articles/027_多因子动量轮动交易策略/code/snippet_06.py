def adjust_position_sell(context, buy_stocks):
    index_signal = get_index_signal(g.index_pool)
    for stock in context.portfolio.positions:
        current_data = get_current_data()
        now_price = current_data[stock].last_price
        # 根据不同条件进行卖出操作
        if index_signal == '000016.XSHG' and now_price < context.portfolio.positions[stock].avg_cost * 0.85:
            order_target(stock, 0)  # 大盘股跌幅超过15%止损
            log.info('大盘股跌幅超15%止损卖出: ' + str(stock))
        elif index_signal == '399303.XSHE' and now_price < context.portfolio.positions[stock].avg_cost * 0.95:
            order_target(stock, 0)  # 小盘股跌幅超过5%止损
            log.info('小盘股跌幅超5%止损卖出: ' + str(stock))
        elif stock not in buy_stocks:
            order_target(stock, 0)  # 不在买入列表中的股票卖出
            log.info('卖出不在买入列表中的股票: ' + str(stock))
