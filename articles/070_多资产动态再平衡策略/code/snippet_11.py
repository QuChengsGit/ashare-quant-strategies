def rebalance(context, asset_alloc):
    new_asset_values = {}
    new_asset_ratio = cal_stocks_ratio(context, asset_alloc)
    for stock in asset_alloc:
        new_asset_values[stock] = context.portfolio.total_value * new_asset_ratio[stock]
    sell_stocks = []
    for stock in context.portfolio.positions:
        if stock not in new_asset_values:
            order_target_value(stock, 0)
            sell_stocks.append(stock)
        elif new_asset_values[stock] < context.portfolio.positions[stock].value:
            order_target_value(stock, new_asset_values[stock])
            sell_stocks.append(stock)
    for stock in new_asset_values:
        if stock not in sell_stocks:
            order_target_value(stock, new_asset_values[stock])
    g.rebalanced_asset_values = new_asset_values

复制
