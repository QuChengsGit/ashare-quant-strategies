def hold_check(context):
    N = 20
    for stk in context.portfolio.positions:
        stk_dict = context.portfolio.positions[stk]
        if stk_dict.closeable_amount == 0:
            continue
        dt = attribute_history(stk, N+2, '60m', ['close'])
        dt['man'] = dt.close / dt.close.rolling(N).mean()
        if dt.man[-1] >= 1.0:
            continue
        log.info("盘中止损，卖出：{}".format(stk))
        close_position(stk_dict)
