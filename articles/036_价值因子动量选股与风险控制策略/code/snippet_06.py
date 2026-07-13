def check_limit_up(context):
    if not g.no_trading_today_signal:
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count and position_count != 0:
            my_Trader(context)  # 重新计算股票池
            cdata = get_current_data()
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in g.choice:
                if s not in context.portfolio.positions and s not in g.just_sold:
                    order = order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break
        # 获取昨日涨停的股票列表
        current_data = get_current_data()
        if g.high_limit_list:
            for stock in g.high_limit_list:
                if current_data[stock].last_price < current_data[stock].high_limit:
                    order_target(stock, 0)
                    g.just_sold.append(stock)
