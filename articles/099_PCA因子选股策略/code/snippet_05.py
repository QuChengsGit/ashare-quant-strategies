def TradeFunc(context):
    trade_date = context.previous_date
    if trade_date in g.factor_df.index.levels[0]:
        if g.factor_name == 'pca_pv':
            pca = PCA(n_components=1)
            v = g.factor_df.loc[trade_date].fillna(0).values
            pca_v = pca.fit_transform(v)
            pca_pv = pd.DataFrame(pca_v,
                                  index=g.factor_df.loc[trade_date].index,
                                  columns=['pca_pv'])
            frame = -pca_pv['pca_pv']  # 取相反，pca_pv低5组最好
        else:
            frame = g.factor_df.loc[trade_date, g.factor_name]
        if g.is_in_index is None:
            target_code = frame.nsmallest(g.hold_num).index.tolist()
        else:
            cons_symbol = get_index_stocks(g.is_in_index)
            target_code = frame.reindex(cons_symbol).nsmallest(
                g.hold_num).index.tolist()
        for hold in context.portfolio.long_positions:
            if hold not in target_code:
                order_target(hold, 0)
        every_stock = context.portfolio.total_value / len(target_code)
        for stock in target_code:
            order_target_value(stock, every_stock)
