def filter_paused_stock(stock_list):
    # 过滤掉停牌股票
    return [stock for stock in stock_list if not get_current_data()[stock].paused]

复制
