def sellstock(context, sell_list):
    current_data = get_current_data()
    for security in sell_list:
        cprice = current_data[security].last_price
        boughtcost = context.portfolio.positions[security].acc_avg_cost
        profit = (cprice - boughtcost) / boughtcost * 100
        log.info("卖出 %s " % (current_data[security].name), "收益: %.1f%%" % profit)
        limit_price = max(cprice * 0.95, current_data[security].low_limit)
        order_target_value(security, 0, LimitOrderStyle(limit_price))

复制
