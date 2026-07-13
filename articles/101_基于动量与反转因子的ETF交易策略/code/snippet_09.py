def check_stop_loss(context, etf):
    position = context.portfolio.positions[etf]
    current_price = attribute_history(etf, 1, '1d', ['close'])['close'][-1]
    stop_price = position.avg_cost * (1 - g.stop_loss_pct)
    return current_price < stop_price
