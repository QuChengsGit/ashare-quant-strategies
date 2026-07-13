def get_stocks(context):
    by_date = context.previous_date - datetime.timedelta(days=180)
    stocks = get_all_securities(date=by_date).index.tolist()
    stocks = filter_all_stocks(context, stocks)
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    stocks = get_peg(context, stocks)
    stocks = filter_highprice_stock(context, stocks)
    g.buylist = stocks[:g.stock_num]
