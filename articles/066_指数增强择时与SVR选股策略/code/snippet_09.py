def today_prepare(context):
    n_position = g.stock_num
    n_choice = int(1.2 * n_position)
    cdata = get_current_data()
    dt_last = context.previous_date
    index_list = ['399101.XSHE']  # 中小板综指
    stocks = _get_stocks(index_list, dt_last)
    q = query(
            valuation.code,
            valuation.market_cap, 
            valuation.pb_ratio > 0,
            indicator.inc_return > 0,
            indicator.inc_total_revenue_year_on_year > 0,
            indicator.inc_net_profit_year_on_year > 0,
            indicator.ocf_to_operating_profit > 5,
        ).filter(
            valuation.code.in_(stocks),
            balance.total_assets > balance.total_liability,
            income.net_profit > 0,
        )
    df = get_fundamentals(q, dt_last).fillna(0).set_index('code')
    df.columns = ['log_mc', 'log_NC', 'log_NI', 'log_RD', 'PE', 'OCF']
    svr = SVR(kernel='rbf')
    Y = df['log_mc']
    X = df.drop('log_mc', axis=1)
    model = svr.fit(X, Y)
    r = Y - pd.Series(svr.predict(X), Y.index)
    r = r[r < 0].sort_values().head(n_choice)
    choice = r.index.tolist()
    if g.curstaut == 0:
        if g.timing_signal == "BUY":
            g.check_out_list = choice
            g.curstaut = 1
        else:
            g.check_out_list = []
    else:
        if g.timing_signal == "SELL":
            g.check_out_list = []
            g.curstaut =
 0
        else:
            g.check_out_list = choice
