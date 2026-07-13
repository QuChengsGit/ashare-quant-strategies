def get_stock_rank_m_m(stock_list):
    rank_stock_list = DataFrame(stock_list)
    rank_stock_list.rename(columns={0: 'code'}, inplace=True)
    rank_stock_list['circulating_market_cap'] = [get_fundamentals(query(valuation).filter(valuation.code == stock)).iloc[0]['circulating_market_cap'] for stock in rank_stock_list['code']]
    rank_stock_list['market_cap'] = [get_fundamentals(query(valuation).filter(valuation.code == stock)).iloc[0]['market_cap'] for stock in rank_stock_list['code']]
    volume_days_sum = [attribute_history(stock, g.volume_days, '1d', 'volume', df=False)['volume'].sum() for stock in rank_stock_list['code']]
    increase_period = [get_growth_rate(g.increase_days, stock) for stock in rank_stock_list['code']]
    current_price = [get_close_price(stock, 1, '1m') for stock in rank_stock_list['code']]
    min_price = min(current_price)
    min_increase_period = min(increase_period)
    min_volume = min(volume_days_sum)
    min_circulating_market_cap = min(rank_stock_list['circulating_market_cap'])
    min_market_cap = min(rank_stock_list['market_cap'])
    totalcount = [[i,
                   math.log(min_price / current_price[i]) * g.score_weights[0] +
                   math.log(min_volume / volume_days_sum[i]) * g.score_weights[1] +
                   math.log(min_increase_period / increase_period[i]) * g.score_weights[2] +
                   math.log(min_circulating_market_cap / rank_stock_list['circulating_market_cap'][i]) * g.score_weights[3] +
                   math.log(min_market_cap / rank_stock_list['market_cap'][i]) * g.score_weights[4]
                   ] for i in rank_stock_list.index]
    totalcount.sort(key=lambda x: x[1])
    final_list = [rank_stock_list['code'][totalcount[-1 - i][0]] for i in range(min(g.sellrank, len(rank_stock_list)))]
    stock_list = final_list
    return stock_list
