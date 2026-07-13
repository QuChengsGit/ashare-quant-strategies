def buy(context):
    current_data = get_current_data()
    value = context.portfolio.total_value / g.ps
    for s in g.target_list:
        if context.portfolio.available_cash / current_data[s].last_price > 100:
            if current_data[s].last_price == current_data[s].high_limit:
                order_value(s, value, LimitOrderStyle(current_data[s].day_open))
            else:
                order_value(s, value, MarketOrderStyle(current_data[s].day_open))
            print('买入' + s)

复制
