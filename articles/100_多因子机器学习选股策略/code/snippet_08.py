def BuyStock(context, target):
    everyStock = context.portfolio.total_value / len(target)
    for buy_stock in target:
        order_target_value(buy_stock, everyStock)
def SellStock(context, target):
    for hold_stock in context.portfolio.long_positions:
        if hold_stock not in target:
            order_target(hold_stock, 0)
