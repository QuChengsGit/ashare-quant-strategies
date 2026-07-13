def fun_calc_trade_ratio(context):
    equity_ES, equity_ratio = __fun_calc_stock_risk_ES(g.equity)
    commodities_ES, commodities_ratio = __fun_calc_stock_risk_ES(g.commodities)
    bonds_ES, bonds_ratio = __fun_calc_stock_risk_ES(g.bonds)
    money_fund_ES, money_fund_ratio = __fun_calc_stock_risk_ES(g.money_fund)
    max_ES = max(equity_ES, commodities_ES, bonds_ES, money_fund_ES)
    equity_position = max_ES / equity_ES if equity_ES else 0
    commodities_position = max_ES / commodities_ES if commodities_ES else 0
    bonds_position = max_ES / bonds_ES if bonds_ES else 0
    money_fund_position = max_ES / money_fund_ES if money_fund_ES else 0
    total_position = equity_position + commodities_position + bonds_position + money_fund_position
    __ratio = {}
    __ratio = __fun_calc_trade_ratio(__ratio, g.equity, equity_ratio, equity_position, total_position)
    __ratio = __fun_calc_trade_ratio(__ratio, g.commodities, commodities_ratio, commodities_position, total_position)
    __ratio = __fun_calc_trade_ratio(__ratio, g.bonds, bonds_ratio, bonds_position, total_position)
    __ratio = __fun_calc_trade_ratio(__ratio, g.money_fund, money_fund_ratio, money_fund_position, total_position)
    log.info('仓位:%s' % __ratio)
    return __ratio
def __fun_calc_stock_risk_ES(stock_list):
    __stock_ratio = {}
    if stock_list:
        __stock_ratio[stock_list[0]] = 1
    __portfolio_ES = __fun_get_portfolio_ES(__stock_ratio, '1d', 120, g.confidence_level)
    if math.isnan(__portfolio_ES):
        __portfolio_ES = 0
    return __portfolio_ES, __stock_ratio
def __fun_get_portfolio_ES(ratio, freq, lag, confidence_level):
    a = (1 - 0.99) if confidence_level == 2.58 else (1 - 0.95)
    ES = 0
    if ratio:
        daily_returns = __fun_getdailyreturn(list(ratio.keys())[0], freq, lag)
        dailyReturns_sort = sorted(daily_returns)
        sum_value = sum(dailyReturns_sort[:int(lag * a)])
        ES = -(sum_value / (lag * a)) if sum_value else 0
    return ES

复制
