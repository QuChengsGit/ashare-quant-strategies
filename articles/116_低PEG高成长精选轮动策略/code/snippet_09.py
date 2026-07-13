high_growth_list = get_high_growth_stocks(context, candidate_list)
g.buy_list = high_growth_list[:g.total_stock_num * 2]


get_high_growth_stocks 用营收增速、扣非净利润增速、PE 与 PEG 挑高成长性价比个股。
