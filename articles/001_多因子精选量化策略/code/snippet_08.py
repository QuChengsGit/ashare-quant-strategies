def close_account(context):
    if g.no_trading_today_signal and g.hold_list:
        for stock in g.hold_list:
            close_position(context.portfolio.positions[stock])
            log.info(f"卖出[{stock}]")
def print_position_info(context):
    for position in context.portfolio.positions.values():
        log.info(f"代码: {position.security}，持仓(股): {position.total_amount}，市值: {position.value}，收益率: {100 * (position.price / position.avg_cost - 1):.2f}%")
