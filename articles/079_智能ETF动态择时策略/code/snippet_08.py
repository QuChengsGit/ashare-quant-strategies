def check_etf(context):
    if len(g.not_ipo_list) == 0:
        return 
    idxs = []
    yesterday = context.previous_date
    list_date = get_N_trade_date(yesterday, g.lag)  
    all_funds = get_all_securities(types='fund', date=yesterday) 
    all_idxes = get_all_securities(types='index', date=yesterday) 
    for idx in g.not_ipo_list:
        if idx in all_idxes.index:
            if all_idxes.loc[idx].start_date <= list_date:  
                symbol = g.not_ipo_list[idx]
                if symbol in all_funds.index:
                    if all_funds.loc[symbol].start_date <= list_date:
                        g.available_indexs.append(idx)  
                        idxs.append(idx)
    for idx in idxs:
        del g.not_ipo_list[idx]
    log.info('输出不可交易基金列表：')    
    log.info(g.not_ipo_list)

复制
