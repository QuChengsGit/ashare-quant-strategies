def get_trade_target(context):
    dt = context.current_dt
    ret = []
    for asset in g.pool:
        stock_pool = g.pool[asset]['codes']
        target_stocks = []
        for stocks in stock_pool:
            cur_stocks_isOK = False
            for start_dt in stocks.values():
                if dt >= start_dt:
                    cur_stocks_isOK = True
                    break
            if cur_stocks_isOK:
                target_stocks = [k for k in stocks.keys()]
                break
        ret.extend(target_stocks)
    return ret
