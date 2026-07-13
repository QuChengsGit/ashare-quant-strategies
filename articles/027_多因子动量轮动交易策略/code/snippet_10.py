def filter_stock(context):
    curr_data = get_current_data()
    yesterday = context.previous_date
    by_date = yesterday - datetime.timedelta(days=1200)  # 过滤次新股（3年以内上市的股票）
    initial_list = get_all_securities(date=by_date).index.tolist()
    filtered_list = [stock for stock in initial_list if not (
        (curr_data[stock].day_open == curr_data[stock].high_limit) or
        (curr_data[stock].day_open == curr_data[stock].low_limit) or
        curr_data[stock].paused or
        'ST' in curr_data[stock].name or
        '*' in curr_data[stock].name or
        '退' in curr_data[stock].name or
        stock.startswith('688'))]
    return filtered_list

复制
