# 106、动量轮动与市场择时综合策略

该策略结合了动量因子轮动、市场择时信号（RSRS和MA信号）以及个股止损和止盈机制。通过动量因子对股票池进行筛选，并结合RSRS和MA信号对大盘趋势进行择时。同时，采用线性回归分析对个股进行择时，结合止损和止盈规则来控制风险，确保在风险可控的情况下实现稳健的收益。

### 1. **初始化函数 (initialize)**

该函数在策略启动时进行全局变量的初始化及交易设置。

```python
def initialize(context):
    set_benchmark('000300.XSHG')  # 设置沪深300为基准指数
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 打开防未来数据选项
    set_slippage(FixedSlippage(0.001))  # 设置滑点为0.1%
    set_order_cost(OrderCost(close_tax=0.001, close_commission=0.00015, min_commission=5), type='stock')  # 设置交易费用
    log.set_level('order', 'error')  # 设置日志等级为error，减少不必要的信息输出
```

**说明** ：该函数主要负责初始化交易环境，包括基准指数、价格设置、滑点、佣金和日志设置。

### 2. **选股模块 (get_stock_pool, get_rank)**

**功能** ：从多个热门行业中筛选符合市值要求的股票池，并根据动量因子进行评分排名。

```python
def get_stock_pool():
    # 选取热门行业概念并筛选符合条件的股票池
    concept_names = [...]
    # 获取各行业的股票代码
    all_concepts = get_concepts()
    concept_codes = [code for name in concept_names for code in all_concepts[all_concepts['name'] == name].index]
    all_concept_stocks = [get_concept_stocks(code) for code in concept_codes]
    # 查询市值范围在30亿到1000亿之间的股票
    q = query(valuation.code).filter(valuation.market_cap >= 30, valuation.market_cap <= 1000)
    stock_df = get_fundamentals(q)
    stock_pool = stock_df['code'].tolist()
    # 过滤创业板、科创板、ST股票和停牌股票
    stock_pool = filter_st_stock(filter_paused_stock(stock_pool))
    return stock_pool
```

**说明** ：从热门行业中筛选市值符合要求的股票，过滤掉创业板、科创板、ST及停牌股票。

```python
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
```

**说明** ：基于过去100个交易日的收盘价计算动量因子（年化收益）和R²值，进行评分和排序，返回前5名股票。

### 3. **择时模块 (get_ols, initial_slope_series, get_zscore, get_timing_signal)**

**功能** ：计算RSRS和MA信号，结合大盘信号与个股信号进行择时。

```python
def get_ols(x, y):
    # 线性回归计算斜率、截距和拟合度R²
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (np.sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return intercept, slope, r2
```

**说明** ：该函数进行简单的线性回归，计算股票价格的斜率和拟合度，用于RSRS信号的计算。

```python
def initial_slope_series():
    # 初始化前M日的斜率序列
    data = attribute_history('000300.XSHG', g.N + g.M, '1d', ['high', 'low'])
    return [get_ols(data.low[i:i+g.N], data.high[i:i+g.N])[1] for i in range(g.M)]
```

**说明** ：通过过去M日的最高价和最低价计算斜率，用于RSRS模型的初始化。

```python
def get_zscore(slope_series):
    # 计算斜率序列的标准分
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std
```

**说明** ：计算斜率的标准分，用于衡量股票动量的强度。

```python
def get_timing_signal(stock, rank_stock_diff, context):
    # 计算RSRS和MA信号，判断是否买入、卖出或持仓
    close_data = attribute_history('000300.XSHG', g.mean_day + g.mean_diff_day, '1d', ['close'])
    today_MA = close_data.close[g.mean_diff_day:].mean()
    before_MA = close_data.close[:-g.mean_diff_day].mean()
    high_low_data = attribute_history('000300.XSHG', g.N, '1d', ['high', 'low'])
    intercept, slope, r2 = get_ols(high_low_data.low, high_low_data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2  # 修正标准分
    # 个股的择时判定
    stock_dif = rank_stock_diff.loc[stock]
    sig = np.sum((stock_dif < 0).astype(int))
    if sig < 2:
        return "BUY"
    elif sig >= 2:
        return "SELL"
    else:
        return "KEEP"
```

**说明** ：通过RSRS和MA信号，以及连续下降的股票动量，综合判断是否买入、卖出或保持。

### 4. **过滤模块 (filter_paused_stock, filter_st_stock, filter_limitup_stock, filter_limitdown_stock)**

**功能** ：过滤掉停牌、ST、涨停和跌停的股票，保证投资的流动性和安全性。

```python
def filter_paused_stock(stock_list):
    # 过滤掉停牌股票
    return [stock for stock in stock_list if not get_current_data()[stock].paused]
```

**说明** ：去除掉停牌的股票，避免选择不可交易的股票。

```python
def filter_st_stock(stock_list):
    # 过滤ST及退市股票
    return [stock for stock in stock_list if not get_current_data()[stock].is_st]
```

**说明** ：去除ST股票，避免选择有退市风险的股票。

### 5. **交易模块 (order_target_value_, open_position, close_position, adjust_position)**

**功能** ：执行交易操作，包括开仓、平仓、调整持仓等。

```python
def order_target_value_(security, value):
    return order_target_value(security, value)
```

**说明** ：下单函数，处理买入或卖出的报单。

```python
def open_position(security, value):
    order = order_target_value_(security, value)
    if order and order.filled > 0:
        return True
    return False
```

**说明** ：开仓操作，买入指定价值的证券。

```python
def close_position(position):
    order = order_target_value_(position.security, 0)
    return order and order.status == OrderStatus.held and order.filled == order.amount
```

**说明** ：平仓操作，卖出持有的证券。

```python
def adjust_position(context, buy_stock, stock_position):
    value = context.portfolio.cash / (g.stock_tobuy - len(context.portfolio.positions))
    open_position(buy_stock, value)
```

**说明** ：调整持仓，根据现金余额分配购买金额，开仓或平仓。

### 6. **止损止盈模块 (check_lose, check_profit)**

**功能** ：根据设定的止损和止盈规则，控制交易风险。

```python
def check_lose(context):
    for position in context.portfolio.positions.values():
        if (position.price / position.avg_cost - 1) * 100 <= -15:
            order_target_value(position.security, 0)  # 触发止损
```

**说明** ：如果亏损超过设定阈值（如15%），则触发止损操作。

```python
def check_profit(context):
    for position in context.portfolio.positions:
        highest = attribute_history(position.security, g.sec_data_num, '1d', 'high').max()
        if position.price < highest * (1 - g.take_profit):
            close_position(position)  # 触发止盈
```

**说明** ：若股票价格低于最高点的止盈线，则触发止盈操作。

### 7. **复盘模块 (print_trade_info)**

**功能** ：打印每日的交易记录和账户信息，辅助复盘。

```python
def print_trade_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print(f'成交记录：{_trade}')
    for position in context.portfolio.positions.values():
        print(f'代码:{position.security}，成本价:{position.avg_cost}，现价:{position.price}')
```

**说明** ：每天打印交易的详细记录，包括股票代码、成本、现价、盈亏等信息，便于复盘和分析。



### 总结：

此策略结合了动量因子、RSRS与MA信号的择时方法、以及个股止损和止盈机制，构建了一个稳健的量化交易系统。通过动量因子筛选潜力股票，利用市场择时信号调仓，同时设置止损和止盈规则，确保策略在复杂市场环境下的风险控制和长期稳定的回报。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
