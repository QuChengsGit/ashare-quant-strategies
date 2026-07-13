def print_position_info(context):
    trades = get_trades()
    for t in trades.values(): print('成交记录：'+str(t))
    for pos in context.portfolio.positions.values():
        sec = pos.security
        cost = pos.avg_cost
        price = pos.price
        ret = 100*(price/cost-1)
        value = pos.value
        amount = pos.total_amount
        print(f'代码:{sec}, 成本价:{cost:.2f}, 现价:{price:.2f}, 收益率:{ret:.2f}%, 持仓(股):{amount}, 市值:{value:.2f}')

复制
