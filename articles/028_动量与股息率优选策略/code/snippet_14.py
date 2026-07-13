def check_limit_up(context):
    cdata = get_current_data()
    sell_list = []
    for stock in g.high_limit_list:
        if cdata[stock].last_price < cdata[stock].high_limit:
            log.info("[%s]涨停打开，卖出" % cdata[stock].name)
            sell_list.append(stock)
    if sell_list:
        sellstock(context, sell_list)

复制
