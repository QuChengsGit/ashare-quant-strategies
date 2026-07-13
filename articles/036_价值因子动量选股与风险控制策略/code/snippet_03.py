def go_Trader(context):
    if not g.no_trading_today_signal:
        g.just_sold = []  # 每月清空已卖出的股票列表
        cdata = get_current_data()
        choice = g.choice
        # 卖出不在选股池中的股票
        for s in context.portfolio.positions:
            if s not in choice:
                log.info('Sell', s, cdata[s].name)
                order_target(s, 0)
        # 买入新的股票
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count:
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in choice:
                if s not in context.portfolio.positions:
                    log.info('buy', s, cdata[s].name)
                    order = order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break
