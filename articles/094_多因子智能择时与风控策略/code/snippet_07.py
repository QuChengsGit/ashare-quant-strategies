def risk_management(context):
    if context.current_dt.year < 2020:
        return
    for stock in context.portfolio.positions.keys():
        fuying = context.portfolio.positions[stock].price / context.portfolio.positions[stock].avg_cost - 1
        current_data = get_current_data()
        nosell_1 = context.portfolio.positions[stock].price >= current_data[stock].high_limit
        if fuying < -0.065 and not nosell_1:
            close_position(stock)
    if context.portfolio.total_value < max(g.value) * 0.70:
        g.stop_run = True
        log.info("当前策略净值回撤达到30%, 策略可能失效，需要清仓后做重新评估")
        for stock in context.portfolio.positions.keys():
            if not nosell_1:
                close_position(stock)
