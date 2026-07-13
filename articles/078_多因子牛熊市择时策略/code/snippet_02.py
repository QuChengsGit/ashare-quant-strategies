def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, 'close')['close'][0]
# 获取牛熊信号
def get_bull_bear_signal_minute():
    nowindex = get_close_price(g.MA[0], 1, '1m')
    MAold = (attribute_history(g.MA[0], g.MA[1] - 1, '1d', 'close', True)['close'].sum() + nowindex) / g.MA[1]
    if g.isbull:
        if nowindex * (1 + g.threshold) <= MAold:
            g.isbull = False
    else:
        if nowindex > MAold * (1 + g.threshold):
            g.isbull = True
# 返回股票的中文名称
def get_stock_name(stock_code):
    if g.stocks_allnames_df.loc[g.stocks_allnames_df.index == stock_code].empty:
        return '名称未知'
    return g.stocks_allnames_df.loc[g.stocks_allnames_df.index == stock_code]['display_name'][0]
