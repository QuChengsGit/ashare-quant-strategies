def market_open(context):
    if not g.signal:
        return
    buylist = filter_limit_stock(context, g.alllist)[:g.stock_num]
    for stock in context.portfolio.positions:
        if stock not in buylist and stock not in g.high_limit_list:
            order = order_target_value(stock, 0)
            if order is not None:
                log.info(f'卖出股票：{stock} 下单数量：{order.amount} 成交数量：{order.filled}')
    target_num = len(buylist)
    if target_num <= 0:
        return
    value = context.portfolio.total_value / target_num
    for stock in buylist:
        order = order_target_value(stock, value)
        if order is not None:
            log.info(f'调仓：{stock} 调整至金额：{value} 下单数量：{order.amount} 成交数量：{order.filled}')
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close','high_limit'], count=1, panel=False)
            if current_data.iloc[0]['close'] < current_data.iloc[0]['high_limit']:
                order = order_target_value(stock, 0)
                if order is not None:
                    log.info(f'涨停打开-卖出股票：{stock} 下单数量：{order.amount} 成交数量：{order.filled}')
            else:
                log.info(f'{stock} 涨停，继续持有')
    g.high_limit_list = []
