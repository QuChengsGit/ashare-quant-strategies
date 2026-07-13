def change_position(context, target_list):
    # 卖出当前持仓
    hold_list = list(context.portfolio.positions)
    for etf in hold_list:
        order_target_value(etf, 0)
        print(f'卖出 {etf}')
    # 买入目标股票
    if g.stock_number > 0:
        value = context.portfolio.available_cash / g.stock_number
        for etf in target_list:
            if context.portfolio.positions[etf].total_amount == 0:
                order_target_value(etf, value)
                print(f'买入 {etf}')

复制
