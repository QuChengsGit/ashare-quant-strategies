def high_limit_filter(context, security_list):
    current_data = get_current_data()
    security_list = [stock for stock in security_list if not (current_data[stock].last_price == current_data[stock].high_limit)]
    return security_list

复制
