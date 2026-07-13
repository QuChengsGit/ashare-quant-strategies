def slist(context, stock_list):
    current_data = get_current_data()
    for stock in stock_list:
        df = get_fundamentals(query(valuation).filter(valuation.code == stock))
        print('股票代码：{0}, 名称：{1}, 总市值:{2:.2f}, 流通市值:{3:.2f}, PE:{4:.2f}, 股价：{5:.2f}'.format(
            stock, get_security_info(stock).display_name,
            df['market_cap'][0], df['circulating_market_cap'][0],
            df['pe_ratio'][0], current_data[stock].last_price))
