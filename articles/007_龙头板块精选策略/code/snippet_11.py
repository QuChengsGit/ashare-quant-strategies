def sell(context):
    hold_list = list(context.portfolio.positions)
    current_data = get_current_data()
    for s in hold_list:
        if not current_data[s].last_price == current_data[s].high_limit:
            if context.portfolio.positions[s].closeable_amount != 0:
                start_date = transform_date(context.portfolio.positions[s].init_time, 'str')
                target_date = get_shifted_date(start_date, 2, 'T')
                current_date = transform_date(context.current_dt, 'str')
                cost = context.portfolio.positions[s].avg_cost
                price = context.portfolio.positions[s].price
                ret = 100 * (price / cost - 1)
                if current_date >= target_date or ret > 0:
                    if current_data[s].last_price > current_data[s].low_limit:
                        order_target_value(s, 0)
                        print('卖出' + s)

复制
