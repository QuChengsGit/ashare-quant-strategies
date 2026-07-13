def check_limit_up(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info(f"[{stock}]涨停打开，卖出")
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info(f"[{stock}]涨停，继续持有")
