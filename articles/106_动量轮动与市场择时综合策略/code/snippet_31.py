def check_profit(context):
    for position in context.portfolio.positions:
        highest = attribute_history(position.security, g.sec_data_num, '1d', 'high').max()
        if position.price < highest * (1 - g.take_profit):
            close_position(position)  # 触发止盈

复制
