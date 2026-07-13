def get_high_growth_stocks(context, stock_codes):
    yesterday = context.previous_date
    q = query(
        income.code,
        income.operating_revenue,
        indicator.adjusted_profit,
        valuation.pe_ratio,
        valuation.market_cap
    ).filter(
        income.code.in_(stock_codes),
        valuation.pe_ratio <= 30,
        valuation.pe_ratio > 0,
        indicator.adjusted_profit > 0,
    )
    now_df = get_fundamentals(q, date=yesterday)
    lastyear_same_day = datetime.date(yesterday.year - 1, yesterday.month, yesterday.day)
    lastyear_q = query(
        income.code,
        income.operating_revenue,
        indicator.adjusted_profit,
        valuation.pe_ratio
    ).filter(
        income.code.in_(now_df['code'].values.tolist())
    )
    lastyear_df = get_fundamentals(lastyear_q, date=lastyear_same_day)
    merged_df = pd.merge(now_df, lastyear_df, on='code', suffixes=['', '_lastyear'])
    merged_df['growth_operating_revenue'] = (merged_df['operating_revenue'] - merged_df['operating_revenue_lastyear']) / abs(merged_df['operating_revenue_lastyear'])
    merged_df['growth_adjusted_profit'] = (merged_df['adjusted_profit'] - merged_df['adjusted_profit_lastyear']) / abs(merged_df['adjusted_profit_lastyear'])
    merged_df['peg'] = merged_df['pe_ratio'] / (merged_df['growth_adjusted_profit'] * 100)
    df = merged_df.loc[(merged_df['peg'] <= 1) & (merged_df['growth_adjusted_profit'] > 0) & (merged_df['growth_operating_revenue'] >= 0.15), :]
    df = df.sort_values(by='market_cap')
    return list(df['code'])
