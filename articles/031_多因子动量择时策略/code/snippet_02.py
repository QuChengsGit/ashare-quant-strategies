def trade(context):
    stock_hold = set(context.portfolio.positions.keys())
    stock_pool = get_stock_pool()
    g.stock_number = g.stock_num if len(stock_pool) > g.stock_num else len(stock_pool)
    set_stock_pool = set(stock_pool[:g.stock_num])
    print(f'持仓股票: {stock_hold}')
    print(f'待买入股票: {set_stock_pool}')
    signal = get_signal()
    print(f'当前信号: {signal}')
    if stock_pool and signal != "SELL":
        if stock_hold == set_stock_pool and len(set_stock_pool) != 0:
            print("当前持仓与目标一致，无需调仓")
        else:
            change_position(context, set_stock_pool)
    else:
        if signal == "SELL":
            print("RSRS择时模型发出清仓信号！")
        for stock in stock_hold:
            order_target_value(stock, 0)
    log.info('今日交易完成')
    log.info('##############################################################')
