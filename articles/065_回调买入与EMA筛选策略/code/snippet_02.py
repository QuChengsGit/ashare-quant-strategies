def filter_specials(context, stock_list):
    """
    过滤特定类型的股票：
    1. 涨停、跌停、停牌股票；
    2. ST、*ST、退市股票；
    3. 创业板、科创板股票；
    4. 次新股。
    """
    curr_data = get_current_data()
    stock_list = [stock for stock in stock_list if not (
        curr_data[stock].paused or  # 停牌
        curr_data[stock].is_st or  # ST股票
        ('ST' in curr_data[stock].name) or
        ('*' in curr_data[stock].name) or
        ('退' in curr_data[stock].name) or
        (stock.startswith('688'))  # 科创板股票
    )]
    return stock_list
def before_trading_start(context):
    # 获取市值前500的股票并过滤特定股票
    fundamentals_data = get_fundamentals(query(valuation.code, valuation.market_cap).order_by(valuation.market_cap.asc()).limit(g.choice))
    g.stock_pool = list(fundamentals_data['code'])
    g.stock_pool = filter_specials(context, g.stock_pool)
