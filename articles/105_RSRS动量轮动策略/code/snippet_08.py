def my_trade(context):
    loss_ctrl(context)
    if context.portfolio.positions_value == 0:
        order_value('511880.XSHG', context.portfolio.available_cash)
def loss_ctrl(context):
    if g.max_value is None:
        g.max_value = context.portfolio.total_value
    if g.last_value is None:
        g.last_value = context.portfolio.total_value
    k = context.portfolio.total_value / g.last_value - 1
    if k < -0.02:
        for code in context.portfolio.positions:
            order_target(code, 0)
        log.info('市值极速下跌清仓')
    k = context.portfolio.total_value / g.max_value - 1
    if k < -0.1:
        for code in context.portfolio.positions:
            order_target(code, 0)
        log.info('最大市值下跌清仓')
        g.max_value = context.portfolio.total_value
    if context.portfolio.total_value > g.max_value:
        g.max_value = context.portfolio.total_value
    g.last_value = context.portfolio.total_value
