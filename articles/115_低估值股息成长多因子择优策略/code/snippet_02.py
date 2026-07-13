def get_stocks(context):
    # 剔除上市不足180天的新股
    all_stocks = list(get_all_securities(['stock']).index)
    stock_list = [s for s in all_stocks
                  if (context.current_dt.date() - get_security_info(s).start_date).days > 180]
    # 过滤ST、退市、停牌、涨跌停股票
    stock_list = filter_all_stocks(context, stock_list)
    # 筛选高股息率股票
    stock_list = get_dividend_ratio_filter_list(context, stock_list, limit=0.25)
    # 筛选PEG低的股票
    stock_list = get_peg(context, stock_list)
    # 过滤高价股
    stock_list = filter_highprice_stock(context, stock_list)
    # 取前20只股票
    g.buylist = stock_list[:g.stock_num]
    log.info("选股完成，共选出{}只股票".format(len(g.buylist)))
