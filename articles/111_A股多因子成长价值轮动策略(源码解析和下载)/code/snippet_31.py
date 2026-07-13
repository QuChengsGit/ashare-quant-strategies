df = pd.DataFrame(index=initial_list)
    df['operating_revenue_growth_rate'] = list(factor_values['operating_revenue_growth_rate'].T.iloc[:,0])
    df['total_profit_growth_rate'] = list(factor_values['total_profit_growth_rate'].T.iloc[:,0])
    df['earnings_growth'] = list(factor_values['earnings_growth'].T.iloc[:,0])

复制
