def epo(x, signal, lambda_, method="simple", w=None, anchor=None, normalize=True, endogenous=True):
    assert isinstance(method, str), "`method` must be a string."
    assert isinstance(lambda_, (int, float)), "`lambda` must be a number."
    assert isinstance(w, (int, float)), "`w` must be a number."
    assert isinstance(normalize, bool), "`normalize` must be a boolean."
    if method == "anchored" and anchor is None:
        raise ValueError("When the `anchored` method is chosen the `anchor` can't be `None`.")
    n = x.shape[1]
    vcov = x.cov()  # 计算协方差矩阵
    corr = x.corr()  # 计算相关系数矩阵
    I = np.eye(n)
    V = np.zeros((n, n))
    np.fill_diagonal(V, vcov.values.diagonal())  # 提取协方差矩阵的对角线（方差）
    std = np.sqrt(V)  # 计算标准差矩阵
    s = signal
    a = anchor
    # Shrinkage相关性矩阵
    shrunk_cor = ((1 - w) * corr.values) + (w * I)  # Shrinkage相关性矩阵
    cov_tilde = std @ shrunk_cor @ std  # 计算Shrinkage协方差矩阵
    inv_shrunk_cov = solve(cov_tilde, np.eye(n))  # 求解逆协方差矩阵
    # 根据方法选择计算EPO权重
    if method == "simple":
        epo = (1 / lambda_) * inv_shrunk_cov @ signal  # 简单EPO方法
    elif method == "anchored":
        if endogenous:
            gamma = np.sqrt(a.T @ cov_tilde @ a) / np.sqrt(s.T @ inv_shrunk_cov @ cov_tilde @ inv_shrunk_cov @ s)
            epo = inv_shrunk_cov @ (((1 - w) * gamma * s) + (w * V @ a))
        else:
            epo = inv_shrunk_cov @ (((1 - w) * (1 / lambda_) * s) + (w * V @ a))
    else:
        raise ValueError("`method` not accepted. Try `simple` or `anchored` instead.")
    # 归一化权重
    if normalize:
        epo = np.maximum(0, epo)  # 确保权重为正
        epo = epo / np.sum(epo)  # 归一化
    return epo
