def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get
_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
    for position in list(context.portfolio.positions.values()):
        print(f"代码:{position.security} 成本价:{format(position.avg_cost,'.2f')} 现价:{position.price} 收益率:{format(100*(position.price/position.avg_cost-1),'.2f')}% 持仓(股):{position.total_amount} 市值:{format(position.value,'.2f')}")
    print('——————分割线————')

复制
