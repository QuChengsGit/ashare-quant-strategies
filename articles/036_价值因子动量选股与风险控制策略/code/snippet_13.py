# 获取PEG因子并筛选股票
def get_peg(context, stocks):
    q = query(valuation.code,
              valuation.pe_ratio / indicator.inc_net_profit_year_on_year,  # PEG因子
              indicator.roe / valuation.pb_ratio,  # PB-ROE因子
              indicator.roe,
              valuation.pb_ratio).filter(
                  valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 0,
                  valuation.pb_ratio < 3,
                  valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q, date=None)
    stocks = list(df_fundamentals.code)
    df = get_fundamentals(query(valuation.code).filter(valuation.code.in_(stocks)).order_by(valuation.market_cap.asc()))
    return list(df.code)
# 获取股息率并筛选股票
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365)
    interval = 1000
    list_len = len(stock_list)
    q = query(finance.STK_XR_XD.code,
              finance.STK_XR_XD.a_registration_date,
              finance.STK_XR_XD.bonus_amount_rmb).filter(
                  finance.STK_XR_XD.a_registration_date >= time0,
                  finance.STK_XR_XD.a_registration_date <= time1,
                  finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)]))
    df = finance.run_query(q)
    if list_len > interval:
        df_num = list_len // interval
        for i in range(df_num):
            q = query(finance.STK_XR_XD.code,
                      finance.STK_XR_XD.a_registration_date,
                      finance.STK_XR_XD.bonus_amount_rmb).filter(
                          finance.STK_XR_XD.a_registration_date >= time0,
                          finance.STK_XR_XD.a_registration_date <= time1,
                          finance.STK_XR_XD.code.in_(stock_list[interval * (i + 1):min(list_len, interval * (i + 2))]))
            temp_df = finance.run_query(q)
            df = df.append(temp_df)
    dividend = df.fillna(0).set_index('code').groupby('code').sum()
    temp_list = list(dividend.index)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(temp_list))
    cap = get_fundamentals(q, date=time1).set_index('code')
    DR = pd.concat([dividend, cap], axis=1, sort=False)
    DR['dividend_ratio'] = (DR['bonus_amount_rmb'] / 10000) / DR['market_cap']
    DR = DR.sort_values(by=['dividend_ratio'], ascending=sort)
    return list(DR.index)[int(p1 * len(DR)):int(p2 * len(DR))]

复制
