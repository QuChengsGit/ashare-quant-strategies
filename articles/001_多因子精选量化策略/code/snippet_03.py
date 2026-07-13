def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities('stock', yesterday).index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    final_list = []
    for factor_list, coef_list in g.factor_list:
        factor_values = get_factor_values(initial_list, factor_list, end_date=yesterday, count=1)
        df = pd.DataFrame({factor: factor_values[factor].iloc[0] for factor in factor_list}, index=initial_list)
        df = df.dropna()
        # 计算因子得分
        df['total_score'] = sum(coef_list[i] * df[factor_list[i]] for i in range(len(factor_list)))
        df = df.sort_values(by='total_score', ascending=False)
        # 进一步筛选基本面良好的股票
        selected_stocks = list(df.index)[:int(0.1 * len(df))]
        q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(selected_stocks)).order_by(valuation.circulating_market_cap.asc())
        df = get_fundamentals(q)
        df = df[df['eps'] > 0]
        filtered_stocks = filter_paused_stock(list(df.code))
        filtered_stocks = filter_limitup_stock(context, filtered_stocks)
        filtered_stocks = filter_limitdown_stock(context, filtered_stocks)
        final_list.extend(filtered_stocks[:g.stock_num])
    return final_list
