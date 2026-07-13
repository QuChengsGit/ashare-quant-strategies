def get_high_limit(context):
    g.high_limit_list = []
    current_data = get_current_data()
    for stock in context.portfolio.positions:
        price = current_data[stock].last_price
        if price >= current_data[stock].high_limit:
            g.high_limit_list.append(stock)
def check_high_limit(context):
    current_data = get_current_data()
    for stock in g.high_limit_list:
        if current_data[stock].last_price < current_data[stock].high_limit:
            order_target_value(stock, 0)
            log.info("开板卖出 {}".format(stock))
