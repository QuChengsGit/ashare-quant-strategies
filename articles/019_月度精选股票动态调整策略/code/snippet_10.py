def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (current_data[stock].is_st or 'ST' in current_data[stock].name or '*' in current_data[stock].name or '退' in current_data[stock].name)]
