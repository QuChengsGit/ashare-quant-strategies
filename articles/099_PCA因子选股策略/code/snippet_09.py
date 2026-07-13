def set_variables():
    g.factor_df = pd.read_csv(BytesIO(read_file('cpv.csv')),
                              index_col=[0, 1],
                              parse_dates=['date'])

复制
