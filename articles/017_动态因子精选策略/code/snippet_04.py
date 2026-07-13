def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limit_stock(context, target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in target_list if stock not in black_list]
    if len(target_list) > 10:
        target_list = target_list[:10]
    h_ma = history(20 + 20, '1d', 'close', target_list).rolling(window=20).mean().iloc[20:]
    X = np.arange(len(h_ma))
    tmp_target_list = []
    for stock in target_list:
        MA_N_Arr = h_ma[stock].values
        MA_N_Arr = MA_N_Arr - MA_N_Arr[0]
        slope = round(sm.OLS(MA_N_Arr, X).fit().params[0] * 100, 1)
        remove_it = False
        if slope < -2:
            if stock not in g.hold_list:
                print('{}下降趋势明显，切勿开仓'.format(stock))
                remove_it = True
        if not remove_it:
            tmp_target_list.append(stock)
    target_list = tmp_target_list
    gupiao = [get_security_info(s).display_name for s in target_list]
    print("提示买的股票列表%s" % gupiao)
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % stock)
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持有[%s]" % stock)
    position_count = len(context.portfolio.positions)
    target_num = g.stock_num
    if target_num > position_count:
        value = context.portfolio.available_cash / (target_num - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) >= g.stock_num:
                        break
