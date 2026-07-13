def Trade(context):
    bar_time = context.current_dt.date()
    if bar_time in g.stocks_df.index:
        target_stocks = g.stocks_df.loc[bar_time].values.tolist()
        SellStock(context, target_stocks)
        BuyStock(context, target_stocks)

复制
