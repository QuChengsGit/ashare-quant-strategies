# 判断ETF的RSRS斜率是否高于历史Beta
def is_above_beta(context, etf):
    hl = attribute_history(etf, 18, '1d', ['high', 'low'])
    slope = np.polyfit(hl['low'], hl['high'], 1)[0]
    beta = calculate_beta(context, etf)
    return slope > beta

复制
