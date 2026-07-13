def analyze_stocks_held(context):
    current_data = get_current_data()
    hold_stocks = context.portfolio.positions.keys()
    for s in hold_stocks:
        q = query(valuation.code, valuation.market_cap, valuation.pe_ratio, indicator.inc_net_profit_year_on_year).filter(valuation.code == s)
        df = get_fundamentals(q)
        log.info(s, current_data[s].name, '市盈率', df['pe_ratio'][0])
        log.info(s, current_data[s].name, '净利润同比增长率', df['inc_net_profit_year_on_year'][0])
    log.info('一天结束')
def after_trading_end(context):
    g.total_value = context.portfolio.total_value
    if g.total_value > g.new_high_value:
        g.new_high_value = g.total_value
        g.maxdown = 0
    else:
        max_down = (g.new_high_value - g.total_value) / g.new_high_value * 100
        g.maxdown = max_down if max_down > g.maxdown else g.maxdown
    record(maxdown=g.maxdown)
