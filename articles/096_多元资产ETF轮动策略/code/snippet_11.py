def ETF_trade(context):
    if len(g.sells) > 0:
        for code in g.sells:
            log.info("卖出: %s" % code)
            order_target(code, 0)
    if len(g.purchases) > 0:
        for code in g.purchases:
            log.info('买入: %s' % code)
            order_target(code, g.df_etf[g.df_etf['基金代码'] == code]['股数'].values)

复制
