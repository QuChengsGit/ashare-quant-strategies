def my_trade(context):
    adjust_position(context, g.check_out_lists)
def adjust_position(context, buy_stocks):
    sellbuystocklist = []
    advlist_s = []
    for stock in g.hold_list:
        if (stock not in buy_stocks) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            sellbuystocklist.append(stock)
            advlist_s.append("卖出"+str(position.total_amount)+"股")
            close_position(position)
        else:
            log.info("已持有[%s]" % (stock))
    # 根据剩余仓位进行买入操作
    position_count = len(context.portfolio.positions)
    if g.buy_stock_count > position_count:
        value = context.portfolio.cash / (g.buy_stock_count - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    sellbuystocklist.append(stock)
                    advlist_s.append("买入"+str(context.portfolio.positions[stock].total_amount)+"股")
                    if len(context.portfolio.positions) == g.buy_stock_count:
                        break
    send_mail(context, sellbuystocklist, advlist_s, '大市值价值投资-调仓通知', '调仓通知')
