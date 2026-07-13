def pre_hold_check(context):
    if context.portfolio.positions:
        for stk in context.portfolio.positions:
            dt = attribute_history(stk, g.lossN + 2, '60m', ['close'])
            dt['man'] = dt.close / dt.close.rolling(g.lossN).mean()
            if dt.man[-1] < 1.0:
                log.info("盘中可能止损，卖出：{}".format(stk))
                send_message("盘中可能止损，卖出：{}".format(stk))

复制
