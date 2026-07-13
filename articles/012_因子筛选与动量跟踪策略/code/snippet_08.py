def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print(f'代码: {securities}\n成本价: {cost:.2f}\n现价: {price}\n收益率: {ret:.2f}%\n持仓(股): {amount}\n市值: {value:.2f}\n{"—"*50}')
    print(f'{"—"*50}分割线{"—"*50}')
