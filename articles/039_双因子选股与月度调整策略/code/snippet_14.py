# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
# 过滤ST及其他具有退市标签的股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
            current_data[stock].is_st or
            'ST' in current_data[stock].name or
            '*' in current_data[stock].name or
            '退' in current_data[stock].name)]
# 过滤涨停和跌停的股票
def filter_limit_stock(context, stock_list):
    current_data = get_current_data()
    holdings = list(context.portfolio.positions)
    return [stock for stock in stock_list if (stock in holdings) or
            current_data[stock].low_limit < current_data[stock].last_price < current_data[stock].high_limit]
# 过滤科创板股票
def filter_kcb_stock(stock_list):
    return [stock for stock in stock_list if not stock.startswith('68')]

复制
