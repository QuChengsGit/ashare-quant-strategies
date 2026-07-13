def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
    for position in context.portfolio.positions.values():
        print('代码:{}'.format(position.security))
        print('成本价:{}'.format(format(position.avg_cost, '.2f')))
        print('现价:{}'.format(position.price))
        print('收益率:{}%'.format(format(100 * (position.price / position.avg_cost - 1), '.2f')))
        print('持仓(股):{}'.format(position.total_amount))
        print('市值:{}'.format(format(position.value, '.2f')))
        print('———————————————————————————————————')

复制
