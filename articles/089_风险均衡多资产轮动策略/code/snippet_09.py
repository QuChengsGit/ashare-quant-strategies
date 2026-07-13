def rebalance(context):
    trade_ratio = fun_calc_trade_ratio(context)
    g.trade_ratio = trade_ratio
    for stock in trade_ratio:
        if stock in context.portfolio.positions:
            g.positions[stock] = context.portfolio.positions[stock].price
        else:
            g.positions[stock] = 0.0
def fun_trade(context, buyDict):
    def __fun_tradeStock(_context, _stock, ratio):
        total_value = _context.portfolio.total_value
        curPrice = history(1, '1d', 'close', _stock, df=False)[_stock][-1]
        curValue = _context.portfolio.positions[_stock].total_amount * curPrice if _stock in _context.portfolio.positions else 0.0
        Quota = total_value * ratio
        deltaValue = abs(Quota - curValue)
        if deltaValue / Quota >= 0.25 and deltaValue > 1000:
            if Quota > curValue:
                if curPrice > g.transactionRecord[_stock]['avg_cost']:
                    cash = _context.portfolio.available_cash
                    if cash >= Quota * 0.25:
                        g.QuantLib.fun_trade(_context, _stock, Quota)
            else:
                g.QuantLib.fun_trade(_context, _stock, Quota)
    for stock in buyDict.keys():
        __fun_tradeStock(context, stock, buyDict[stock])

复制
