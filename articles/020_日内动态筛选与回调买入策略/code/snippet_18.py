def before_trading_start(context):
    log.info('------------------------------------------------------------')
    fundamentals_data = get_fundamentals(query(valuation.code, valuation.market_cap).order_by(valuation.market_cap.asc()).limit(g.choice))
    stocks = list(fundamentals_data['code'])
    current_data = get_current_data()
    g.muster = [s for s in stocks if not current_data[s].paused and not current_data[s].is_st and 'ST' not in current_data[s].name and '*' not in current_data[s].name and '退' not in current_data[s].name and current_data[s].low_limit < current_data[s].day_open < current_data[s].high_limit]
    g.muster = filter_paused_stock(g.muster)
    g.muster = filter_st_stock(g.muster)
    g.muster = filter_kcbj_stock(g.muster)
    g.muster = filter_limitup_stock(context, g.muster)
    g.muster = filter_limitdown_stock(context, g.muster)

复制
