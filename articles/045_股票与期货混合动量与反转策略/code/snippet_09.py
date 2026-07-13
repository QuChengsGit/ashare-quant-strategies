def market_trade_future(context):
    g.sign = update_niu_signal(context, g.benchmark)
    g.loss_stop = loss_stop(context, g.benchmark)
    g.volatility = volatility(context, g.benchmark)
    # 根据波动率调整持仓手数
    if g.volatility == -1:
        future_position = int(1.5 * g.k)
    elif g.volatility == 1:
        future_position = int(1 * g.k)
    # 开仓信号
    if (len(context.subportfolios[1].long_positions) == 0) & (len(context.subportfolios[1].short_positions) == 0):
        if g.sign > 0:
            order(g.code_1, future_position, side='long', pindex=1)
        elif g.sign < 0:
            order(g.code_1, future_position, side='short', pindex=1)
    # 平仓信号
    elif (len(context.subportfolios[1].long_positions) + len(context.subportfolios[1].short_positions)) > 0:
        if g.de_day == 0:
            # ATR止损
            if (len(context.subportfolios[1].long_positions) > 0) & (g.loss_stop == 1):
                order_target(g.code_1, 0, side='long', pindex=1)
            elif (len(context.subportfolios[1].short_positions) > 0) & (g.loss_stop == 1):
                order_target(g.code_1, 0, side
='short', pindex=1)
            # 平开仓信号
            elif (len(context.subportfolios[1].long_positions) > 0) & (g.sign == 0):
                order_target(g.code_1, 0, side='long', pindex=1)
                order(g.code_1, future_position, side='short', pindex=1)
            elif (len(context.subportfolios[1].short_positions) > 0) & (g.sign > 0):
                order_target(g.code_1, 0, side='short', pindex=1)
                order(g.code_1, future_position, side='long', pindex=1)
        else:
            # 交割日平仓
            if len(context.subportfolios[1].long_positions) > 0:
                order_target(g.code_1, 0, side='long', pindex=1)
            else:
                order_target(g.code_1, 0, side='short', pindex=1)

复制
