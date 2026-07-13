def show_cap(context):
    current_data = get_current_data()
    hold_stocks = context.portfolio.positions.keys()
    for s in hold_stocks:
        q = query(valuation).filter(valuation.code == s)
        df = get_fundamentals(q)
        log.info(s, current_data[s].name, '市值', df['market_cap'][0], '亿')
        log.info(s, current_data[s].name, '股价', current_data[s].last_price, '元')
