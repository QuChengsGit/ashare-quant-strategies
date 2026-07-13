def get_rank(stock_pool, context):
    # 基于年化收益和判定系数进行打分排名
    stock_dict_list = []
    for stock in stock_pool:
        data = get_price(stock, end_date=context.current_dt, count=100, frequency="120m", fields=["close"])
        data = data.dropna()
        # 使用线性回归计算动量因子的斜率，计算年化收益
        y = np.log(data["close"])
        x = np.arange(len(y))
        slope = (y.iloc[-1] - y.iloc[0]) / 29  # 计算动量斜率
        annualized_returns = math.pow(math.exp(slope), 250) - 1  # 年化收益
        r_squared = 1 - (np.sum((y - (slope * x + intercept)) ** 2) / ((29 - 1) * np.var(y, ddof=1)))  # 判定系数
        score = annualized_returns * np.abs(r_squared)
        stock_dict_list.append({get_security_info(stock).display_name: score})
    stock_df = pd.DataFrame.from_dict({k: v for d in stock_dict_list for k, v in d.items()}, orient='index')
    stock_df = stock_df.sort_values(by=[0], ascending=False)
    return stock_df.index.values[:5], stock_df['code'].values[:5], stock_df
