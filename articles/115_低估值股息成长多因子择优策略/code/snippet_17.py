def filter_all_stocks(context, stock_list):
    current_data = get_current_data()
    result = []
    for stock in stock_list:
        info = get_security_info(stock)
        if stock.startswith(('68', '4', '8')):  # 剔除科创板、北交所
            continue
        if current_data[stock].paused:  # 停牌
            continue
        if current_data[stock].is_st or 'ST' in info.display_name or '*' in info.display_name or '退' in info.display_name:
            continue
        price = current_data[stock].last_price
        if price == current_data[stock].high_limit or price == current_data[stock].low_limit:
            continue
        result.append(stock)
    return result

复制
