def handle_data(context, data):
    if g.days % g.refresh_rate == 0:
        sample = get_index_stocks('000985.XSHG', date=None)
        sample = filter_stock_ST(sample)
        sample = remove_new_stocks(sample, context)
        sample = filter_stock_limit(sample)
        q = query(valuation.code, 
                  valuation.market_cap, 
                  indicator.roe / valuation.pb_ratio, 
                  valuation.pe_ratio / indicator.inc_net_profit_year_on_year
                 ).filter(
                     valuation.pe_ratio < 100,
                     valuation.market_cap < 1000,
                     valuation.code.in_(sample)
                 ).order_by(
                     (valuation.pe_ratio / indicator.inc_net_profit_year_on_year).asc()
                 ).limit(500)
        df = get_fundamentals(q, date=None)
        select_list = list(df['code'])
        for factor in g.factors:
            df[factor] = np.array(eval(factor)(select_list, end_date=None))
        momentum = []
        for i in select_list:
            interval, Yesterday = getStockPrice(i, g.refresh_rate)
            stock_momentum = Yesterday / interval - 1
            momentum.append((i, stock_momentum))
        np_momentuma = np.array(momentum)
        momentum_value = np_momentuma[:, 1].astype(float).tolist()
        df['momentum_value'] = momentum_value
        df.columns = ['code', 'market_cap', 'PB_ROE', 'PE_G', g.factors[0], g.factors[1], g.factors[2], 'momentum_value']
        df = df_neutralization(df, 'market_cap')
        df.index = df.code.values
        del df['code']
        df = df.fillna(0)
        X = df[g.factors]
        Y = df[['market_cap']]
        X = X.fillna(0)
        Y = Y.fillna(0)
        svr = SVR(kernel='poly', gamma=0.01)
        model = svr.fit(X, Y)
        predict = svr.predict(X)
        record(R2=r2_score(Y, predict))
        record(MAE=mean_absolute_error(Y, predict))
        record(MSE=mean_squared_error(Y, predict))
        record(EVS=explained_variance_score(Y, predict))
        factor = Y - pd.DataFrame(predict, index=Y.index, columns=['market_cap'])
        factor = factor.sort_index(by='market_cap', ascending=True)
        order_list = fisher_transform_strategy(context, list(factor.index))[:g.stocknum]
        order_stock_sell(context, order_list)
        order_stock_buy(context, order_list)
        g.days += 1
    else:
        g.days += 1
