def get_dividend_ratio_filter_list(context, stock_list, limit=0.25):
    end_date = context.current_dt.date()
    start_date = end_date - timedelta(days=365)
    # 查询分红数据
    df = finance.run_query(
        query(finance.STK_XR_XD.code, finance.STK_XR_XD.cash_div).filter(
            finance.STK_XR_XD.code.in_(stock_list),
            finance.STK_XR_XD.announcement_date >= start_date,
            finance.STK_XR_XD.announcement_date <= end_date))
    df = df.groupby('code')['cash_div'].sum().reset_index()
    # 获取市值数据
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(stock_list))
    df_val = get_fundamentals(q)
    merged = pd.merge(df, df_val, on='code')
    merged['dividend_yield'] = merged['cash_div'] / merged['market_cap']
    # 按股息率排序
    merged = merged.sort_values('dividend_yield', ascending=False)
    count = int(len(merged) * limit)
    return list(merged.iloc[:count]['code'])

复制
