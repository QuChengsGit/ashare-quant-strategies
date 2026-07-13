def market_open(context):
    tar_mon = context.current_dt.date().strftime('%Y-%m')
    if g.if_trade is True:
        if tar_mon in g.df_dic:
            log.info(f'############## tar mon：{str(tar_mon)} today: {str(context.current_dt.date())} ##############')
            stock_df = g.df_dic[tar_mon]
            rebalance(context, stock_df)
        g.if_trade = False
