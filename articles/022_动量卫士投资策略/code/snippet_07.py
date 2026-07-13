def select_stocks_and_buy(context):
    select_stocks(context)
    choice = g.buylist
    buy_stocks(context, g.buylist)
def select_stocks(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    q = query(valuation.code,
                valuation.pe_ratio / indicator.inc_net_profit_year_on_year,
                indicator.roe / valuation.pb_ratio,
                indicator.roe).filter(
                    valuation.pe_ratio / indicator.inc_net_profit_year_on_year > -1,
                    valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 3,
                    valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q, date=None)
    stocks = list(df_fundamentals.code)
    q = query(valuation.code, valuation.market_cap).filter(
        valuation.code.in_(stocks),
        valuation.market_cap <= 100).order_by(valuation.market_cap.asc())
    df = get_fundamentals(q, date=None)
    choice = list(df.code)
    choice = filter_st_stock(choice)
    choice = filter_paused_stock(choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    choice = choice[:g.stock_num * 2]
    g.buylist = choice
def buy_stocks(context, choice):
    position_count = len(context.portfolio.positions)
    if g.stock_num <= position_count:
        return
    buylist = choice
    psize = context.portfolio.available_cash / (g.stock_num - position_count)
    for s in buylist:
        if s not in context.portfolio.positions:
            log.info('buy', s)
            order_value(s, psize)
            if len(context.portfolio.positions) == g.stock_num:
                break

复制
