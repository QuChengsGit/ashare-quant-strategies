g.buy_list = filter_limitup_stock(context, g.buy_list)
g.buy_list = g.buy_list[:min(g.total_stock_num, len(g.buy_list))]

复制
