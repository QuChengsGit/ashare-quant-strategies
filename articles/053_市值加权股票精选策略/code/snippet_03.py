def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock.startswith('4') or stock.startswith('8') or stock.startswith('68'))]
# 过滤ST及退市风险股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st
            and 'ST' not in current_data[stock].name
            and '*' not in current_data[stock].name
            and '退' not in current_data[stock].name]
