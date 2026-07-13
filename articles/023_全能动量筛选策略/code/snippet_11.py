def weekly_adjustment(context):
    g.not_buy_again = []
    target_list = g.target_list
    target_list = target_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.yesterday_HL_list):
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("持有[%s]" % (stock))
    buy_security(context,target_list)
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.not_buy_again.append(stock)

复制
