# 定义获取数据并调用优化函数的函数
def run_optimization(stocks, end_date):
    prices = get_price(stocks, count=1200, end_date=end_date, frequency='daily', fields=['close'])['close']
    returns = prices.pct_change().dropna()  # 计算收益率
    d = np.diag(returns.cov())  # 获取每个资产的方差
    a = (1/d) / (1/d).sum()  # 计算基准锚点配置
    weights = epo(x=returns, signal=returns.mean(), lambda_=10, method="anchored", w=1, anchor=a)  # 运行EPO优化
    return weights
# 交易
def trade(context):
    end_date = context.previous_date
    weights = run_optimization(g.etf_pool, end_date)  # 获取优化后的权重
    if weights is None:
        return
    total_value = context.portfolio.total_value  # 获取总资产
    for i, weight in enumerate(weights):
        value = total_value * weight  # 计算每个资产的目标投资额
        order_target_value(g.etf_pool[i], value)  # 调整资产权重
