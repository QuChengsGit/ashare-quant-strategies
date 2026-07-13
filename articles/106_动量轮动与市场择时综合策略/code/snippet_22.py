def get_zscore(slope_series):
    # 计算斜率序列的标准分
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std

复制
