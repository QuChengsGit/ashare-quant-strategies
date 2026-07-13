def check_trade(context):
    log.info("-----今天的交易开始了-----------------------------------------")
    df_index = pd.DataFrame(columns=['指数代码', '周期动量'])
    df_incre = pd.DataFrame(columns=['大盘代码','周期涨幅','当前价格'])
    BBI2 = BBI(g.available_indexs, 
               check_date=context.current_dt, 
               timeperiod1=3, 
               timeperiod2=6, 
               timeperiod3=12, 
               timeperiod4=24,
               unit = g.unit,
               include_now=True)
    for index in g.available_indexs:
        df_close = get_bars(index, 1, g.unit, ['close'], end_dt=context.current_dt, include_now=True)['close']
        val = BBI2[index]/df_close[0]
        df_index = df_index.append({'指数代码': index, '周期动量': val}, ignore_index=True)
    df_index.sort_values(by='周期动量', ascending=False, inplace=True)
    log.info("输出排序后的指数代码和周期动量")
    log.info(df_index)
    target = df_index['指数代码'].iloc[-1]
    target_bbi = df_index['周期动量'].iloc[-1]
    for index in g.zs_list:
        df_close = get_bars(index, 2, '1d', ['close'], end_dt=context.current_dt, include_now=True)['close']
        if len(df_close) > 1:
            increase = (df_close[1] - df_close[0]) / df_close[0]
            df_incre = df_incre.append({'大盘指数': index, '周期涨幅': increase, '当前数值': df_close[0]}, ignore_index=True)
    df_incre.sort_values(by='周期涨幅', ascending=False, inplace=True)
    log.info("输出大盘数据")
    log.info(df_incre)
    today_increase = df_incre['周期涨幅'].iloc[0]
    today_index_code = df_incre['大盘代码'].iloc[0]
    today_index_close = df_incre['当前数值'].iloc[0]
    if(today_increase > g.dapan_threshold and target_bbi < 1):
        g.signal = 'BUY'
        g.increase_days += 1
    else:
        g.signal = 'CLEAR'
        g.decrease_days += 1
    holdings = set(context.portfolio.positions.keys()) 
    log.info("-------------increase_days----------- %s" % (g.increase_days))
    log.info("-------------decrease_days----------- %s" % (g.decrease_days))
    target_etf = g.ETF_list[target]
    if(g.signal == 'CLEAR'):
        for etf in holdings:
            log.info("----~~~---指数集体下跌，卖出---~~~~~~-------- %s" % (etf))
            order_target(etf, 0)
            return
    else:
        for etf in holdings:
            if (etf == target_etf):
                log.info('相同etf，不需要调仓！@')
                return 
            else:
                order_target(etf, 0)
                log.info("------------------调仓卖出----------- %s" % (etf))
        log.info("------------------买入----------- %s" % (target))
        order_value(target_etf,context.portfolio.available_cash)

复制
