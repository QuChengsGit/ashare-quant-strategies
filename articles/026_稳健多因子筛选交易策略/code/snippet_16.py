def get_peg(context, stocks):
    q = query(valuation.code).filter(
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year > -3,
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 3,
        valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q)
    stocks = list(df_fundamentals.code)
    df = get_fundamentals(query(valuation.code).filter(valuation.code.in_(stocks)).order_by(valuation.market_cap.asc()))
    return list(df.code)

复制
