def rolling_R2(df_m_shifted_, Ret_mat, window=24):
    datelist = df_m_shifted_.index.unique()
    R2_mat_all = pd.DataFrame(index=Ret_mat.columns.tolist())
    for i in range(window - 1, len(df_m_shifted_)):
        df_m_shifted_i = df_m_shifted_.iloc[(i - window + 1):i, :]
        R2_mat_i = R_squared(df_m_shifted_i, Ret_mat)
        R2_mat_all[datelist[i]] = R2_mat_i
    return R2_mat_all.T
