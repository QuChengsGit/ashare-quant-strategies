def sell_stocks(context, sell_list):
    current_data = get_current_data()
    if len(sell_list) > 0:
        for security in sell_list:
            cprice = current_data[security].last_price
            boughtcost = context.portfolio.positions[security].avg_cost
            if context.portfolio.positions[security].avg_cost == 0:
                log.error("Sell %s " % (current_data[security].name), "avg_cost is 0")
                profit = 0
            else:
                profit = (cprice - boughtcost) / boughtcost * 100
            log.info("Sell %s " % (current_data[security].name), "profit: %.1f%%" % profit)
            limit_price = max(cprice * 0.95, current_data[security].low_limit)
            order_target_value(security, 0, LimitOrderStyle(limit_price))
def sell_stocks_opened_from_up_limit(context):
    cdata = get_current_data()
    sell_list = []
    if len(g.high_limit_list) > 0:
        for stock in g.high_limit_list:
            if cdata[stock].last_price < cdata[stock].high_limit:
                log.info("[%s]涨停打开，卖出" % cdata[stock].name)
                sell_list.append(stock)
    if sell_list:
        sell_stocks(context, sell_list)
def sell_hi_vol_stocks_at_dayend_and_buy_again(context):
    btlist = context.portfolio.positions
    cdata = get_current_data()
    sell_list = []
    for stock in btlist:
        if (cdata[stock].last_price == cdata[stock].high_limit):
            continue
        stock_now_vol = now_vol(context, stock)
        stock_ma10_vol = ma_vol(context, stock, 10)
        if (stock_now_vol > stock_ma10_vol * 3):
            log.info("[%s]放量未涨停，卖出" % cdata[stock].name)
            sell_list.append(stock)
    if sell_list:
        sell_stocks(context, sell_list)
    buy_stocks(context, g.buylist)

复制
