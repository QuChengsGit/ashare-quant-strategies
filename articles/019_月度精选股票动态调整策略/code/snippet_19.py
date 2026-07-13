def check_limit_up(context):
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_current_data()
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info("[%s] 涨停打开，卖出" % (stock))
                order_target(stock, 0)
            else:
                log.info("[%s] 涨停，继续持有" % (stock))

复制
