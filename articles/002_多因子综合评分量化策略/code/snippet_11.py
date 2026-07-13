def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：'+str(_trade))
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount    
        print(f'代码:{securities}')
        print(f'成本价:{format(cost, ".2f")}')
        print(f'现价:{price}')
        print(f'收益率:{format(ret, ".2f")}%')
        print(f'持仓(股):{amount}')
        print(f'市值:{format(value, ".2f")}')
        print('———————————————————————————————————')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
