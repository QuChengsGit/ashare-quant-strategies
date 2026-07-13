def filter_st_stock(stock_list):
    # 过滤ST及退市股票
    return [stock for stock in stock_list if not get_current_data()[stock].is_st]
