def Preprocessing():
    if g.method == 'SVM':
        th = 0.05
        z = 0.1  # 设置阈值和权重调整系数
        GetTargetDf(th, z)
    elif g.method == 'Logistic':
        th = 0.1
        z = 0.2
        GetTargetDf(th, z)
    elif g.method == 'RandomForest':
        th = 0
        z = 0.1
        GetTargetDf(th, z)
    elif g.method == 'not_timing':
        r2 = rolling_R2(g.df_m_shifted_.fillna(0), g.Ret_mat.fillna(0), window=24)
        weight_new = pd.DataFrame(1 / len(g.weight_in.columns), index=r2.index.tolist(), columns=g.weight_in.columns)
        g.stocks_df = get_portfolio(weight_new, g.datas, number=g.N)

复制
