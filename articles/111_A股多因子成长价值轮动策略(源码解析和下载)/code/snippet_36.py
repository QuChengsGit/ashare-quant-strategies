df = df.sort_values(by='total_score', ascending=False)
    complex_growth_list = list(df.index)[:max(int(0.1*len(df)),1)]
