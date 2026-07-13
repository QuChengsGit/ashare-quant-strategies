def check_limit_up(context):
    """
    检查持仓中的涨停股票是否需要卖出
    """
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=context.current_dt, frequency='1m', fields=['close', 'high_limit'])
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:  # 如果不涨停则卖出
                log.info("[%s]涨停打开，卖出" % stock)
                position = context.portfolio.positions[stock]
                close_position(position)
