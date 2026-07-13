def order_func(total_value: float, available_cash: float, fund_price: float):
    order_amount = min(available_cash / fund_price, total_value * g.order_amount)
    order_target_value(g.stock_security, order_amount)
def order_value(stock: str, cash: float):
    order_amount = min(cash, 0.1 * context.portfolio.total_value)
    order_target_value(stock, order_amount)
