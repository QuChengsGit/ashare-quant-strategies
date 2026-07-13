def go_Trader(context):
    if g.no_trading_today_signal == False:
        cdata = get_current_data()
        choice = g.choice
        for s in context.portfolio.positions:
            if s not in choice and not cdata[s].paused:
                log.info('Sell', s, cdata[s].name)
                order_target(s, 0)
                g.just_sold.append(s)
                if len(g.just_sold) >= g.limit_days:
                    g.just_sold = g.just_sold[-g.stock_num:]
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count:
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in choice:
                if s not in context.portfolio.positions:
                    log.info('Buy', s, cdata[s].name)
                    order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break

复制
