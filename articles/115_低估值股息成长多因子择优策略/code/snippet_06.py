def get_peg(context, stocks):
    q = query(valuation.code, valuation.pe_ratio, indicator.inc_net_profit_year_on_year).filter(
        valuation.code.in_(stocks))
    df = get_fundamentals(q)
    # 计算PEG
    df['PEG'] = df['pe_ratio'] / df['inc_net_profit_year_on_year']
    df = df[(df['PEG'] > 0) & (df['PEG'] < 3)]  # 合理区间
    df = df.sort_values('PEG')
    return list(df['code'])
