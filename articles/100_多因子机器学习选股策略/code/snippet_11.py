def set_variables():
    g.Ret_mat = pd.read_csv(BytesIO(read_file('Data/Ret_mat.csv')), index_col=[0], parse_dates=True)
    g.datas = pd.read_csv(BytesIO(read_file('Data/datas.csv')), index_col=[0, 1], parse_dates=True)
    g.df_m_shifted_ = pd.read_csv(BytesIO(read_file('Data/df_m_shifted_.csv')), index_col=[0], parse_dates=True)
    g.weight_in = pd.read_csv(BytesIO(read_file('Data/weight_in.csv')), index_col=[0], parse_dates=True)

复制
