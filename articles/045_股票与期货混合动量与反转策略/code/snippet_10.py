def volatility(context, ind):
    current_ATR_a = ATR(ind, context.current_dt, g.shortdays)
    current_ATR_b = ATR(ind, context.current_dt, g.longdays)
    k = current_ATR_a[-1][ind] - g.para * current_ATR_b[-1][ind]
    if k < 0:
        return -1  # 波动率低，可重仓
    elif k > 0:
        return 1  # 波动率高，可轻仓

复制
