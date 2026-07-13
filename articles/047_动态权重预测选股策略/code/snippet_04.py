def factor_analysis_initialize(context):
    g.sell = pd.Series(dtype=float)
    g.buy = pd.Series(dtype=float)
    g.d = context.previous_date
