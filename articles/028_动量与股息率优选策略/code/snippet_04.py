def buystock(context, choice):
    position_count = len(context.portfolio.positions)
    if g.stock_num <= position_count:
        return
    psize = context.portfolio.available_cash / (g.stock_num - position_count)
    for s in choice:
        if s not in context.portfolio.positions:
            log.info('买入', s, get_current_data()[s].name)
            order_value(s, psize)
            if len(context.portfolio.positions) == g.stock_num:
                break
