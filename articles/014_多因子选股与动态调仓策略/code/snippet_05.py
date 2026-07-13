def check_limit_up(context):
    if g.no_trading_today_signal == False:
        current_data = get_current_data()
        if g.high_limit_list:
            for stock in g.high_limit_list:
                if current_data[stock].last_price < current_data[stock].high_limit:
                    order_target(stock, 0)
                    log.info("[%s]涨停打开，卖出" % stock)
                    g.just_sold.append(stock)
                    if len(g.just_sold) >= g.limit_days:
                        g.just_sold = g.just_sold[-g.stock_num:]
                else:
                    log.info("[%s]涨停，继续持有" % stock)
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count and position_count != 0:
            my_Trader(context)
            cdata = get_current_data()
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in g.choice:
                if s not in context.portfolio.positions:
                    order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break
