recent_limit_up_list = get_recent_limit_up_stock(context, g.buy_list, g.limit_days)
black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
g.buy_list = [stock for stock in g.buy_list if stock not in black_list]
