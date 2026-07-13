high_growth_list = get_high_growth_stocks(context, candidate_list)
g.buy_list = high_growth_list[:g.total_stock_num * 2]
