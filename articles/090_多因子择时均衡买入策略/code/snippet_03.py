def handle_data(context, data):
    current_data = get_current_data()
    # 卖出条件
    for stock in context.portfolio.positions.keys():
        price = data[stock].close
        if context.portfolio.positions[stock].closeable_amount == 0 \
                or current_data[stock].low_limit == price \
                or current_data[stock].high_limit == price:
            continue
        print('%s卖出(自动):自动卖出:成本价:%s,当前价:%s' % (stock, context.portfolio.positions[stock].avg_cost, price))
        sell_stock(stock, 0)
    # 判断是否买满
    if g.buy_stock_limit <= len(context.portfolio.positions.keys()):
        return
    # 买入条件
    for stock in g.buy_list:
        price = data[stock].close
        if context.portfolio.available_cash < (price * 100) \
                or current_data[stock].low_limit == price \
                or current_data[stock].high_limit == price \
                or stock in context.portfolio.positions.keys():
            continue
        print('%s买入(自动):自动买入:当前价:%s' % (stock, price))
        buy_stock(context, stock)
        break
