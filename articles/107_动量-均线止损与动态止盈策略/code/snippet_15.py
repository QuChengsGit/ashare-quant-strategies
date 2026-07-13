def market_open(context):
    print('入选股票:{}'.format(g.stock_list))
    adjust_position(context, g.stock_list)

复制
