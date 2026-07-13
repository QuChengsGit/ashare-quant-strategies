def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            log.info("[%s]已不在应买入列表中" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("[%s]已经持有无需重复买入" % (stock))
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                open_position(stock, value)
                if len(context.portfolio.positions) == g.stock_num:
                    break
def check_lose(context):
    for position in list(context.portfolio.positions.values()):
        if 100 * (position.price / position.avg_cost - 1) <= -90:
            order_target_value(position.security, 0)
            log.info("止损: 标的={}, 浮动盈亏={}%".format(position.security, format(ret, '.2f')))
def print_trade_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
