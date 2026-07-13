def after_market_close(context):
    stock_list = all_limit_up_stocks(context.current_dt.strftime("%Y-%m-%d"))
    consecutive_up_limit_stocks(context,stock_list,context.current_dt)
    day_report(context)
    log.info('##############################################################')
def consecutive_up_limit_stocks(context,stock_list, thisDate):
    cur_data = get_current_data()
    stock_list = list(get_fundamentals(query(valuation.code).filter(valuation.circulating_market_cap<100,valuation.code.in_(stock_list)).order_by(indicator.roe.desc())).code)
    # 其他选股逻辑...
    g.buy_list = limit_stocks

复制
