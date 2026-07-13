def print_trade_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print(f'成交记录：{_trade}')
    for position in context.portfolio.positions.values():
        print(f'代码:{position.security}，成本价:{position.avg_cost}，现价:{position.price}')

复制
