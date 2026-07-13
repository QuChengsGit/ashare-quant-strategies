def check_limit_up(context):
    now_time = context.current_dt
    for stock in g.yesterday_HL_list:
        data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], count=1, panel=False)
        if data.iloc[0, 0] < data.iloc[0, 1]:
            close_position(context.portfolio.positions[stock])
            log.info(f"[{stock}]涨
