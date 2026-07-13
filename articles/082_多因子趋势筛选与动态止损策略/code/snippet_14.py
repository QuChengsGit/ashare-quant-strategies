def generate_stock_pool(context, today_date, lastd_date):
    # 构建基准指数股票池
    stocklist = get_index_stocks(g.index, date=None)
    stocklist = [stockcode for stockcode in stocklist if not get_current_data()[stockcode].paused]
    stocklist = [stockcode for stockcode in stocklist if not get_current_data()[stockcode].is_st]
    stocklist = [stockcode for stockcode in stocklist if '退' not in get_current_data()[stockcode].name]
    stocklist = [stockcode for stockcode in stocklist if (today_date - get_security_info(stockcode).start_date).days > 365]
    return stocklist

复制
