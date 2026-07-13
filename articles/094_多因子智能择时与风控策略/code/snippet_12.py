def get_stock_rank_m_m(stock_list):
    rank_stock_list = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.circulating_market_cap).filter(valuation.code.in_(stock_list)).order_by(valuation.circulating_market_cap.asc()).limit(100))
    volume5d = [attribute_history(stock, 1200, '1m', 'volume', df=False)['volume'].sum() for stock in rank_stock_list['code']]
    increase60d = [get_growth_rate60(stock) for stock in rank_stock_list['code']]
    current_price = [get_close_price(stock, 1, '1m') for stock in rank_stock_list['code']]
    min_price = min(current_price)
    min_increase60d = min(increase60d)
    min_circulating_market_cap = min(rank_stock_list['circulating_market_cap'])
    min_market_cap = min(rank_stock_list['market_cap'])
    min_volume = min(volume5d)
    totalcount = [[i, math.log(min_volume / volume5d[i]) * g.weights[3] + math.log(min_price / current_price[i]) * g.weights[2] + math.log(min_circulating_market_cap / rank_stock_list['circulating_market_cap'][i]) * g.weights[1] + math.log(min_market_cap / rank_stock_list['market_cap'][i]) * g.weights[0] + math.log(min_increase60d / increase60d[i]) * g.weights[4]] for i in rank_stock_list.index]
    totalcount.sort(key=lambda x: x[1])
    return [rank_stock_list['code'][totalcount[-1-i][0]] for i in range(min(g.sellrank, len(rank_stock_list)))]

复制
