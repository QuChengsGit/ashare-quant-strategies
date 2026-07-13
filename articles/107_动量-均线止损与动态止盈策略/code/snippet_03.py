def filter_price_stocks(context, stock_list, limit_count):
    min_price, max_price = g.limit_price[0], g.limit_price[1]
    new_list = []
    cur_data = get_current_data()
    for stock in stock_list:
        cur_price = cur_data[stock].last_price
        if (cur_price > max_price and stock not in context.portfolio.positions) \
            or cur_price < min_price:
            log.info(stock, cur_price, '超出限价范围', g.limit_price)
            continue
        new_list.append(stock)
        if len(new_list) >= limit_count:
            break
    return new_list[:limit_count]
