def print_position_info(context):
    position_percent = 100 * context.portfolio.positions_value / context.portfolio.total_value
    record(仓位=round(position_percent, 2))
    for position in context.portfolio.positions.values():
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print(f'代码:{securities} 成本价:{format(cost, ".2f")} 现价:{price} 收益率:{format(ret, ".2f")}% 持仓(股):{amount} 市值:{format(value, ".2f")}')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
