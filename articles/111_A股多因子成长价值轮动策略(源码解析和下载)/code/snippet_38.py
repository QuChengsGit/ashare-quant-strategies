q = query(valuation.code, valuation.circulating_market_cap, indicator.eps)\
        .filter(valuation.code.in_(complex_growth_list))\
        .order_by(valuation.circulating_market_cap.asc())
    df_final = get_fundamentals(q)
    df_final = df_final[df_final['eps']>0]
    return list(df_final.code)
