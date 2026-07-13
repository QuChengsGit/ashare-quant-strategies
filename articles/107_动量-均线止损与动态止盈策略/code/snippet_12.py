def before_market_open(context):
    all_stock = set()
    # 使用BOLL策略筛选股票
    s1_stocks = Boll399101Strat().get_stock_list(context)
    all_stock.update(filter_price_stocks(context, s1_stocks, 20))
    g.stock_list = list(all_stock)  # 更新今天的持股列表

复制
