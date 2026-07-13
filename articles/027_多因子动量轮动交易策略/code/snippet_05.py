def get_growth_stock_list(context):
    print("小盘业绩炒作风格")
    initial_list = filter_stock(context)
    df = get_fundamentals(query(valuation.code).filter(
        valuation.code.in_(initial_list),
        valuation.pb_ratio > 0,
        indicator.inc_return > 0,
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0,
        indicator.ocf_to_operating_profit > 5,
    ).order_by(valuation.market_cap.asc()))
    choice = list(df.code)[:g.stock_num_small]
    return choice, len(choice)
