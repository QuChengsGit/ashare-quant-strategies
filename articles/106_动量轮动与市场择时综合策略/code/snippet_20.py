def get_ols(x, y):
    # 线性回归计算斜率、截距和拟合度R²
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (np.sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return intercept, slope, r2

复制
