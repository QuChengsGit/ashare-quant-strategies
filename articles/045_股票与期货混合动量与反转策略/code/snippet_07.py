def choice_stocks(context, index, num):
    # 获取指数成分股列表
    stocks = get_index_stocks(index)
    # 过滤并筛选股票
    sdf = get_fundamentals(query(
            valuation.code,
            valuation.market_cap,  # 市值（亿元）
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio < 3,
            valuation.pb_ratio > 0,
            indicator.roe > 0.1,
            balance.cash_equivalents > 0.4 * balance.shortterm_loan,
            indicator.roa > 0.05 * indicator.roe,
            balance.total_assets / balance.total_liability > 1,
            indicator.roa > 0,
            valuation.pe_ratio > 0,
            valuation.ps_ratio > 0,
            valuation.pcf_ratio > 0,
            indicator.inc_revenue_year_on_year > 10,
            indicator.inc_net_profit_to_shareholders_year_on_year > 10,
        )).dropna().set_index('code')
    # 获取最近三年内的分红数据
    dt_3y = context.current_dt.date() - dt.timedelta(days=3*365)
    ddf = finance.run_query(query(
            finance.STK_XR_XD.code,
            finance.STK_XR_XD.company_name,
            finance.STK_XR_XD.board_plan_pub_date,
            finance.STK_XR_XD.bonus_amount_rmb,  # 分红金额（万元）
        ).filter(
            finance.STK_XR_XD.code.in_(stocks),
            finance.STK_XR_XD.board_plan_pub_date > dt_3y,
            finance.STK_XR_XD.bonus_amount_rmb > 0
        )).dropna()
    # 计算股息率
    divy = pd.Series(data=np.zeros(len(stocks)), index=stocks)
    for k in ddf.index:
        s = ddf.code[k]
        divy[s] += ddf.bonus_amount_rmb[k]
    sdf = sdf.reindex(stocks)
    sdf['div_3y'] = divy
    sdf['div_ratio'] = 1e-2 * sdf.div_3y / sdf.market_cap
    sdf = sdf.sort_values(by='div_ratio', ascending=False)
    log.info('\n', sdf[:5])
    return list(sdf.head(num).index)

复制
