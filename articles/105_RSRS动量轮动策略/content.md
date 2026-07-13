# 105、RSRS动量轮动策略

### 策略概述

**RSRS动量轮动策略** 是一个基于动量因子和RSRS（Residual Standardized Residual Score）择时的量化交易策略，主要用于股票市场的投资。策略的核心思想是通过动量因子筛选出表现优异的股票，并结合RSRS择时信号进行买卖决策。策略的目标是在捕捉市场趋势的同时，通过动态止损机制控制风险，实现长期稳定的资产增值。

### 策略详细介绍

1\. 初始化设置

在策略的初始化阶段，进行了以下设置：

```python
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    g.stock_pool = [
        '000300.XSHG', # 沪深300
        '000905.XSHG', # 中证500
        '399006.XSHE', # 创业板
    ]
    g.momentum_day = 29
    g.N = {'000300.XSHG':18, '000905.XSHG':18, '399006.XSHE':18}
    g.M = {'000300.XSHG':700, '000905.XSHG':800, '399006.XSHE':500}
    g.score_threshold = {'000300.XSHG':0.7, '000905.XSHG':1, '399006.XSHE':0.4}
    g.max_value = None
    g.last_value = None
    g.check_out_list = None
    g.timing_signal = None
    set_order_cost(OrderCost(close_tax=0, open_commission=0.00011, close_commission=0.00011, min_commission=5), type='stock')
    set_slippage(FixedSlippage(0.001))
    run_daily(calculate, time='8:00', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(my_trade, time='11:20', reference_security='000300.XSHG')
    run_daily(my_trade, time='14:50', reference_security='000300.XSHG')
```

  * **基准设定** ：将沪深300指数（000300.XSHG）设定为基准。

  * **复权模式** ：开启动态复权模式，使用真实价格进行交易。

  * **防未来函数** ：打开防未来函数，避免使用未来数据。

  * **股票池** ：设定股票池，包含沪深300、中证500和创业板指数。

  * **动量因子参数** ：设定动量因子的参考天数和计算斜率、拟合度的参考天数。

  * **RSRS参数** ：设定RSRS标准分的参考天数和阈值。

  * **手续费设置** ：设定股票交易的手续费。

  * **滑点设置** ：设定滑点为0.001。

  * **运行时间** ：每日8:00计算信号，开盘时进行交易，上午和下午收盘前进行止损操作。

2\. 数据准备

2.1 动量因子筛选

```python
def get_rank(context, stock_pool):
    score_list = []
    for stock in g.stock_pool:
        data = attribute_history(stock, g.momentum_day, '1d', ['close'])
        y = data['log'] = np.log(data.close)
        x = data['num'] = np.arange(data.log.size)
        slope, intercept = np.polyfit(x, y, 1)
        annualized_returns = math.pow(math.exp(slope), 250) - 1
        r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
        score = annualized_returns * r_squared
        score_list.append(score)
    stock_dict = dict(zip(g.stock_pool, score_list))
    sort_list = sorted(stock_dict.items(), key=lambda item: item[1], reverse=True)
    code_list = []
    for i in range((len(g.stock_pool))):
        code_list.append(sort_list[i][0])
    rank_stock = code_list[0]
    return rank_stock
```

  * **动量因子筛选** ：根据动量因子（年化收益和判定系数）对股票池中的股票进行评分，选出评分最高的股票。

2.2 线性回归

```python
def get_ols(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return (intercept, slope, r2)
```

  * **线性回归** ：复现statsmodels的get_OLS函数，用于计算斜率和拟合度。

2.3 因子标准化

```python
def get_zscore(slope_series):
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std
```

  * **因子标准化** ：计算斜率序列的标准分（z-score）。

3\. 交易逻辑

3.1 择时信号

```python
def get_timing_signal(context, stock):
    data = attribute_history(stock, g.M[stock] + g.N[stock], '1d', ['high', 'low', 'close'])
    data['pre_close'] = data.shift(periods=1)['close']
    data['ret'] = data['close'] / data['pre_close'] - 1
    ret_std = data['ret'].rolling(g.N[stock]).std()
    ret_quantile = ret_std.tail(g.M[stock]).rank(pct=True)[-1]
    intercept, slope, r2 = get_ols(data.tail(g.N[stock]).low, data.tail(g.N[stock]).high)
    slope_series = [get_ols(data.low[i:i+g.N[stock]], data.high[i:i+g.N[stock]])[1] for i in range(g.M[stock])]
    slope_series.append(slope)
    zscore = get_zscore(slope_series[-g.M[stock]:])
    rsrs_score = zscore * r2**(2 * ret_quantile)
    if rsrs_score > g.score_threshold[stock]: return "BUY"
    elif rsrs_score < -g.score_threshold[stock]: return "SELL"
    else: return "KEEP"
```

  * **择时信号** ：使用RSRS因子值作为买入、持有和清仓的依据。根据RSRS标准分和阈值判断交易信号。

3.2 提前计算信号

```python
def calculate(context):
    g.check_out_list = get_rank(context, g.stock_pool)
    g.timing_signal = get_timing_signal(context, g.check_out_list)
    print("今天选股：", g.check_out_list)
    print("今天信号：", g.timing_signal)
```

  * **提前计算信号** ：在开盘前计算当天的选股和择时信号。

3.3 开盘交易

```python
def market_open(context):
    stock = list(context.portfolio.positions.keys())
    security = ''.join(stock)
    if g.timing_signal == 'SELL' and security != '511880.XSHG' and security != '':
        if security == g.check_out_list:
            order = order_target_value(security, 0)
        elif get_timing_signal(context, security) == 'SELL':
            order = order_target_value(security, 0)
    elif g.timing_signal == 'BUY' and g.check_out_list != security:
        order_target_value(security, 0)
        order_value(g.check_out_list, context.portfolio.available_cash)
    if context.portfolio.positions_value == 0:
        order_value('511880.XSHG', context.portfolio.available_cash)
```

  * **开盘交易** ：根据择时信号进行调仓，空仓时买入货币基金（如511880.XSHG）。

3.4 止损操作

```python
def my_trade(context):
    loss_ctrl(context)
    if context.portfolio.positions_value == 0:
        order_value('511880.XSHG', context.portfolio.available_cash)
def loss_ctrl(context):
    if g.max_value is None:
        g.max_value = context.portfolio.total_value
    if g.last_value is None:
        g.last_value = context.portfolio.total_value
    k = context.portfolio.total_value / g.last_value - 1
    if k < -0.02:
        for code in context.portfolio.positions:
            order_target(code, 0)
        log.info('市值极速下跌清仓')
    k = context.portfolio.total_value / g.max_value - 1
    if k < -0.1:
        for code in context.portfolio.positions:
            order_target(code, 0)
        log.info('最大市值下跌清仓')
        g.max_value = context.portfolio.total_value
    if context.portfolio.total_value > g.max_value:
        g.max_value = context.portfolio.total_value
    g.last_value = context.portfolio.total_value
```

  * **止损操作** ：在上午和下午收盘前进行止损操作，根据市值的快速下跌和最大市值下跌进行清仓。

### 总结

**RSRS动量轮动策略** 通过动量因子筛选出表现优异的股票，并结合RSRS择时信号进行买卖决策。策略的核心在于通过动量因子捕捉市场的短期趋势，并在趋势确认后进行交易。同时，策略通过动态止损机制控制风险，确保在市场波动中保持资产的稳定增值。总体而言，该策略适合在波动较大的市场中使用，能够有效捕捉短期交易机会，实现资产的增值。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
