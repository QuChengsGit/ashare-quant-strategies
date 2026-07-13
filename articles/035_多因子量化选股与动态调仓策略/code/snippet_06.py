def weekly_adjustment(context):
    all_list = get_stock_list(context)
    sg_list = all_list[0][:5]
    ms_list = all_list[1][:5]
    peg_list = all_list[2][:5]
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(union_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    g.target_list = list(df.code)
    g.target_list = filter_paused_stock(g.target_list)
    g.target_list = filter_limitup_stock(context, g.target_list)
    g.target_list = filter_limitdown_stock(context, g.target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    g.target_list = [stock for stock in g.target_list if stock not in black_list]
    g.target_list = g.target_list[:min(g.stock_num, len(g.target_list))]
    for stock in g.hold_list:
        if stock not in g.target_list and stock not in g.high_limit_list:
            position = context.portfolio.positions[stock]
            close_position(position)
    adjust_position(context, g.target_list, g.stock_num)
