def check_limit_up(context):
    # 检查持仓股票的涨停情况
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info(f"[{stock}] 涨停打开，卖出")
                order_target(stock, 0)
            else:
                log.info(f"[{stock}] 涨停，继续持有")
