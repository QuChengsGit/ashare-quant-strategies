def get_stocks(context):
    current_data = get_current_data()
    stock_chosen = []
    stock_chosen_mom = []
    for stock in g.stocks:
        history_data = attribute_history(stock, unit='1d', count=g.arg_volume_days, fields=['open', 'close', 'volume'])
        history_volume = np.mean(history_data['volume'])
        if np.isnan(history_volume):
            continue
        df_stock_data = get_price(stock, start_date=context.current_dt.replace(hour=9, minute=30, second=0),
                                  end_date=context.current_dt, frequency='1m', fields=['open', 'close', 'high', 'volume'])
        if df_stock_data['volume'].sum() < g.arg_volume_multi * history_volume:
            continue
        if (current_data[stock].last_price - current_data[stock].day_open) / current_data[stock].day_open < g.arg_close_rate:
            continue
        if current_data[stock].high_limit <= df_stock_data['high'].iloc[-1]:
            continue
        Y = df_stock_data['close'].values
        X = sm.add_constant(np.arange(Y.shape[0]))
        ols_result = sm.OLS(Y, X).fit()
        flag_keep_up = (ols_result.rsquared > g.arg_rsquared_min) & (ols_result.params[1] > 0)
        if not flag_keep_up:
            continue
        stock_chosen.append(stock)
        stock_chosen_mom.append((history_data['close'].iloc[-1] - history_data['open'].iloc[-1]) / history_data['open'].iloc[-1])
    stocks = [stock_chosen[i] for i in np.argsort(stock_chosen_mom)[:g.arg_buy_max]]
    log.info(f"可选 {stocks}")
    return stocks
def trade(context):
    g.hold_days += 1
    if g.hold_days < g.arg_hold_max:
        return
    stocks = get_stocks(context)
    for stock in context.portfolio.positions.keys():
        if stock == g.etf:
            continue
        order_target_value(stock, 0)
    count_min = int(g.buy_min_ratio * g.arg_buy_max)
    if len(stocks) < count_min:
        if g.etf:
            order_value(g.etf, context.portfolio.available_cash)
        return
    val = context.portfolio.total_value / (g.arg_buy_max - len(context.portfolio.positions))
    for stock in stocks:
        if len(context.portfolio.positions) >= g.arg_buy_max:
            break
        if g.etf and context.portfolio.available_cash < val and g.etf in context.portfolio.positions:
            order_value(g.etf, -val)
        order_value(stock, val)
    if len(context.portfolio.positions) > 0:
        g.hold_days = 0
    if g.etf:
        order_value(g.etf, context.portfolio.available_cash)
