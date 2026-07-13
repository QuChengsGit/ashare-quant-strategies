def sell(context):
    # 基础信息
    date = transform_date(context.previous_date, 'str')
    current_data = get_current_data()
    # 上午止盈卖出
    if str(context.current_dt)[-8:] == '11:28:00':
        for s in list(context.portfolio.positions):
            if (context.portfolio.positions[s].closeable_amount != 0 and
                current_data[s].last_price < current_data[s].high_limit and
                current_data[s].last_price > context.portfolio.positions[s].avg_cost):
                order_target_value(s, 0)
                log.info(f"止盈卖出: {get_security_info(s, date).display_name} ({s})")
    # 下午止损卖出
    if str(context.current_dt)[-8:] == '14:50:00':
        for s in list(context.portfolio.positions):
            if (context.portfolio.positions[s].closeable_amount != 0 and
                current_data[s].last_price < current_data[s].high_limit):
                order_target_value(s, 0)
                log.info(f"止损卖出: {get_security_info(s, date).display_name} ({s})")
