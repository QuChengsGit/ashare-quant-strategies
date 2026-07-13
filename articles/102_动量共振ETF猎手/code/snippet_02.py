def market_buy(context):
    df_index = pd.DataFrame(columns=['指数代码', '周期动量'])
    df_incre = pd.DataFrame(columns=['大盘代码', '周期涨幅', '当前价格'])
    unit = g.unit
    BBI2 = BBI(g.available_indexs, check_date=context.current_dt, timeperiod1=21, timeperiod2=34, timeperiod3=55, timeperiod4=89, unit=unit, include_now=True)
    for index in g.available_indexs:
        df_close = get_bars(index, 1, unit, ['close'], end_dt=context.current_dt, include_now=True)['close']
        val = BBI2[index] / df_close[0]
        df_index = df_index.append({'指数代码': index, '周期动量': val}, ignore_index=True)
    df_index.sort_values(by='周期动量', ascending=False, inplace=True)
    log.info(df_index)
    target = df_index['指数代码'].iloc[-1]
    target_bbi = df_index['周期动量'].iloc[-1]
    for index in g.zs_list:
        df_close = get_bars(index, 3, '1d', ['close'], end_dt=context.current_dt, include_now=True)['close']
        if len(df_close) > 2:
            increase_previous = (df_close[1] - df_close[0]) / df_close[0]
            increase = (df_close[2] - df_close[1]) / df_close[1]
            increase_delta = (df_close[2] - df_close[1]) / df_close[1] - 0.25 * (df_close[1] - df_close[0]) / df_close[0]
            df_incre = df_incre.append({'大盘代码': index, '前周期涨幅': increase, '本周期涨幅': increase, '本周期涨幅变动': increase_delta, '当前价格': df_close[0]}, ignore_index=True)
    df_incre.sort_values(by='本周期涨幅', ascending=False, inplace=True)
    print(df_incre)
    today_increase_previous = df_incre['前周期涨幅'].iloc[0]
    today_increase = df_incre['本周期涨幅'].iloc[0]
    today_increase_delta = df_incre['本周期涨幅变动'].iloc[0]
    today_index_code = df_incre['大盘代码'].iloc[0]
    today_index_close = df_incre['当前价格'].iloc[0]
    holdings = set(context.portfolio.positions.keys())
    update_niu_signal(context, today_index_code)
    if (context.current_dt.hour == 11 and g.niu_signal == 0 and g.signal == 'BUY') or (context.current_dt.hour == 14 and g.niu_signal == 1):
        log.info('牛熊不匹配，这个时间点不能开仓，并清仓')
        for etf in holdings:
            if etf == g.bond:
                log.info('相同etf，不需要调仓！@')
                return
            else:
                order_target(etf, 0)
                order_value(g.bond, context.portfolio.available_cash)
        return
    if today_increase > g.dapan_threshold and today_increase > 0.05 * today_increase_previous and target_bbi < 1:
        g.signal = 'BUY'
        g.increase_days += 1
    else:
        g.signal = 'CLEAR'
        g.decrease_days += 1
    log.info("-------------increase_days----------- %s" % (g.increase_days))
    log.info("-------------decrease_days----------- %s" % (g.decrease_days))
    target_etf = g.ETF_list[target]
    if g.signal == 'CLEAR':
        for etf in holdings:
            log.info("----~~~---指数集体下跌，卖出---~~~~~~-------- %s" % (etf))
            if etf == g.bond:
                log.info('相同etf，不需要调仓！@')
                return
            else:
                order_target(etf, 0)
                order_value(g.bond, context.portfolio.available_cash)
        return
    else:
        for etf in holdings:
            if etf == target_etf:
                log.info('相同etf，不需要调仓！@')
                return
            else:
                order_target(etf, 0)
                log.info("------------------调仓卖出----------- %s" % (etf))
        log.info("------------------买入----------- %s" % (target))
        order_value(target_etf, context.portfolio.available_cash * g.position)
