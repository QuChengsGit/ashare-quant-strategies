def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)  # 过滤科创板和北交所股票
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)  # 筛选股息率前25%的股票
    stocks = get_peg(context, stocks)  # 进一步根据PEG筛选
    choice = filter_st_stock(stocks)  # 过滤ST股票
    choice = filter_paused_stock(choice)  # 过滤停牌股票
    choice = filter_limitup_stock(context, choice)  # 过滤涨停股票
    choice = filter_limitdown_stock(context, choice)  # 过滤跌停股票
    choice = filter_highprice_stock(context, choice)  # 过滤高价股（股价高于10元）
    g.choice = choice[:g.stock_num]  # 保存最终选股结果

复制
