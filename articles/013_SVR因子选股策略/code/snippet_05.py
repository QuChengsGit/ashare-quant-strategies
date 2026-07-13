def handle_training(context):
    # 参数设置
    n_position = 50  # 持股数
    n_choice = int(1.2 * n_position)  # 选股数，20%缓冲
    index = '399317.XSHE'  # 市场指数
    dt_last = context.previous_date
    # 获取当前市场股票池
    stocks = get_index_stocks(index, dt_last)
    # 获取基础财务数据
    q = query(
        valuation.code,
        valuation.market_cap,
        balance.total_assets - balance.total_liability,
        income.net_profit,
        balance.development_expenditure,
        valuation.pe_ratio,
        balance.total_assets / balance.total_liability,
        indicator.inc_revenue_year_on_year / 100
    ).filter(
        valuation.code.in_(stocks),
        balance.total_assets > balance.total_liability,
        income.net_profit > 0,
    )
    df = get_fundamentals(q, dt_last).fillna(0).set_index('code')
    df.columns = ['log_mc', 'log_NC', 'log_NI', 'log_RD', 'PE', 'lev', 'grow']
    # 对数变换
    def _sign_ln(X):
        return np.sign(X) * np.log(1.0 + np.abs(X))
    df['log_mc'] = _sign_ln(df['log_mc'])
    df['log_NC'] = _sign_ln(df['log_NC'])
    df['log_NI'] = _sign_ln(df['log_NI'])
    df['log_RD'] = _sign_ln(df['log_RD'])
    df['PE'] = _sign_ln(df['PE'])
    df['lev'] = _sign_ln(df['lev'])
    df['grow'] = _sign_ln(df['grow'])
    # 添加行业因子
    industry_list = get_industries('sw_l1', dt_last).index.tolist()
    for sector in industry_list:
        istocks = get_industry_stocks(sector, dt_last)
        s = pd.Series(0, index=df.index)
        s[set(istocks) & set(df.index)] = 1
        df[sector] = s
    # 训练SVR模型
    svr = SVR(kernel='rbf')
    Y = df['log_mc']
    X = df.drop('log_mc', axis=1)
    model = svr.fit(X, Y)
    # 选择具有价值偏差的股票
    residuals = Y - pd.Series(svr.predict(X), index=Y.index)
    choice = residuals[residuals < 0].sort_values().head(n_choice).index.tolist()
    # 保存结果
    g.choice = choice
    g.psize = 1.0 / n_position * context.portfolio.total_value

复制
