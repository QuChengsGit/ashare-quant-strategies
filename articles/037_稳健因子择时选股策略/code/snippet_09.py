def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame({'code': stock_list, 'score': score_list}).dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    return list(df.code)[int(p1 * len(df)):int(p2 * len(df))]

复制
