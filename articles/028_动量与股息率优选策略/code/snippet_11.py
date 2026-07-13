def my_Trader(context):
    stocks = get_all_securities('stock', context.previous_date).index.tolist()
    stocks = filter_kcbj_stock(stocks)  # 过滤科创板和北交所股票
    # 选取高股息率股票
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    # 选取基本面优质股票
    q = query(valuation.code, valuation.pe_ratio / indicator.inc_net_profit_year_on_year, indicator.roe / valuation.pb_ratio, indicator.roe).filter(
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year > -1,
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 3,
        valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q)
    stocks = list(df_fundamentals.code)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(stocks), valuation.market_cap <= 100).order_by(valuation.market_cap.asc())
    df = get_fundamentals(q)
    choice = filter_st_stock(list(df.code))
    choice = filter_paused_stock(choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    g.buylist = choice
    buystock(context, g.buylist)

复制
