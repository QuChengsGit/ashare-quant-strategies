def filter_all_stocks(context, stock_list):
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (
            stock.startswith(('68', '4', '8')) or 
            curr_data[stock].paused or
            curr_data[stock].is_st or
            'ST' in curr_data[stock].name or
            '*' in curr_data[stock].name or
            '退' in curr_data[stock].name or
            curr_data[stock].last_price == curr_data[stock].high_limit or
            curr_data[stock].last_price == curr_data[stock].low_limit
    )]
