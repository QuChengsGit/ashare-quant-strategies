# 31、多因子动量择时策略

# 1. 策略概述

本策略结合RSRS（相对强度回归模型）择时策略与动量因子筛选，通过多因子打分对不同资产类别的ETF进行筛选和排名，并根据择时信号进行调仓，以获取更优的投资收益。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (initialize)

该模块用于设置策略的基本配置，包括基准指数、交易参数以及初始化全局变量。

```python
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 设置滑点为0.004
    set_slippage(FixedSlippage(0.004))
    # 设置交易成本万分之五
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0005, close_commission=0.0005, close_today_commission=0, min_commission=5),
                   type='fund')
    # 仅记录严重错误日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.index_pool = [
        '518880.XSHG',  # 黄金ETF
        '513100.XSHG',  # 纳指100
        '159915.XSHE',  # 创业板100
        '510180.XSHG'   # 上证180
    ]
    g.stock_num = 1  # 持仓股票数量
    g.momentum_day = 25  # 动量计算窗口
    g.stock = '000300.XSHG'  # RSRS模型的标的指数
    g.N = 18  # RSRS模型参数
    g.M = 600  # RSRS模型参数
    g.mean_day = 20  # 均线天数
    g.mean_diff_day = 3  # 均线差异天数
    g.score_threshold = 0.7  # RSRS分值阈值
    g.slope_series = initial_slope_series()[:-1]  # 初始化斜率序列
    # 设置每日交易时间
    run_daily(trade, time='9:45')
```

## 2.2 交易模块 (trade)

该模块用于在每天指定时间执行交易，根据筛选的股票池和择时信号进行调仓操作。

```python
def trade(context):
    stock_hold = set(context.portfolio.positions.keys())
    stock_pool = get_stock_pool()
    g.stock_number = g.stock_num if len(stock_pool) > g.stock_num else len(stock_pool)
    set_stock_pool = set(stock_pool[:g.stock_num])
    print(f'持仓股票: {stock_hold}')
    print(f'待买入股票: {set_stock_pool}')
    signal = get_signal()
    print(f'当前信号: {signal}')
    if stock_pool and signal != "SELL":
        if stock_hold == set_stock_pool and len(set_stock_pool) != 0:
            print("当前持仓与目标一致，无需调仓")
        else:
            change_position(context, set_stock_pool)
    else:
        if signal == "SELL":
            print("RSRS择时模型发出清仓信号！")
        for stock in stock_hold:
            order_target_value(stock, 0)
    log.info('今日交易完成')
    log.info('##############################################################')
```

## 2.3 选股模块 (get_stock_pool)

该模块用于对ETF池中的资产进行筛选和打分，返回排名最高的资产。

```python
def get_stock_pool():
    index_rank = []
    for index in g.index_pool:
        score = get_socre(index)
        index_rank.append((index, score))
    index_rank = sorted(index_rank, key=lambda x: x[1], reverse=True)
    index_dict = dict(index_rank)
    record(黄金=round(index_dict['518880.XSHG'], 2))
    record(纳指=round(index_dict['513100.XSHG'], 2))
    record(成长=round(index_dict['159915.XSHE'], 2))
    record(价值=round(index_dict['510180.XSHG'], 2))
    return tuple(index[0] for index in index_rank)
```

## 2.4 评分模块 (get_socre)

该模块通过计算ETF的年化收益率和判定系数，得出ETF的综合评分。

```python
def get_socre(stock):
    data = attribute_history(stock, g.momentum_day, '1d', ['close'])
    y = data['log'] = np.log(data.close)
    x = data['num'] = np.arange(data.log.size)
    slope, intercept = np.polyfit(x, y, 1)
    annualized_returns = math.pow(math.exp(slope), 250) - 1
    r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return annualized_returns * r_squared
```

## 2.5 调仓模块 (change_position)

该模块根据目标股票池进行调仓操作，卖出当前持仓股票，买入目标股票。

```python
def change_position(context, target_list):
    # 卖出当前持仓
    hold_list = list(context.portfolio.positions)
    for etf in hold_list:
        order_target_value(etf, 0)
        print(f'卖出 {etf}')
    # 买入目标股票
    if g.stock_number > 0:
        value = context.portfolio.available_cash / g.stock_number
        for etf in target_list:
            if context.portfolio.positions[etf].total_amount == 0:
                order_target_value(etf, value)
                print(f'买入 {etf}')
```

## 2.6 信号生成模块 (get_signal)

该模块生成交易信号，基于RSRS模型和均线判断当前的市场状态是买入、卖出还是持仓。

```python
def get_signal():
    close_data = attribute_history(g.stock, g.mean_day + g.mean_diff_day, '1d', ['close'])
    today_MA = close_data.close[g.mean_diff_day:].mean()
    before_MA = close_data.close[:-g.mean_diff_day].mean()
    data = attribute_history(g.stock, g.N, '1d', ['high', 'low'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    if rsrs_score > g.score_threshold and today_MA > before_MA:
        return "BUY"
    elif rsrs_score < -g.score_threshold and today_MA < before_MA:
        return "SELL"
    else:
        return "KEEP"
```

## 2.7 辅助函数

这些函数包括用于初始化斜率序列、计算回归模型、计算标准分等的工具函数。

```python
def get_ols(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return (intercept, slope, r2)
def initial_slope_series():
    data = attribute_history(g.stock, g.N + g.M, '1d', ['high', 'low'])
    return [get_ols(data.low[i:i+g.N], data.high[i:i+g.N])[1] for i in range(g.M)]
def get_zscore(slope_series):
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std
```

通过这一策略，投资者可以在特定的ETF资产池中筛选出最具动量和市场表现的资产，并根据市场信号进行灵活的买卖操作，从而在市场波动中捕捉收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
