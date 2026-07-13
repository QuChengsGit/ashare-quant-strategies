# 11、多维动量择时策略

# 策略概述

“多维动量择时策略”是一种基于动量因子、斜率因子以及市场指数变化的量化交易策略。该策略通过多个维度的技术分析和量化模型，选择最优的ETF进行投资，同时结合大盘趋势、动量变化等指标进行择时和止损，以达到优化投资组合的目的。

# 策略优化与详细代码说明

## 1. 初始化函数

**函数名：initialize**

```python
def initialize(context):
    set_benchmark('399006.XSHE')  # 设定基准为创业板指数
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来数据
    set_slippage(FixedSlippage(0.001))  # 设置固定滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.000, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=0), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志级别
    # 股票池设置
    g.stock_pool = ['510300.XSHG', '510050.XSHG', '159949.XSHE', '159928.XSHE']
    g.stock_num = 1  # 持仓数量
    g.momentum_day = 20  # 动量参考天数
    g.ref_stock = '000300.XSHG'  # 基准指数
    g.N = 18  # 斜率计算参考天数
    g.M = 600  # RSRS标准分计算参考天数
    g.K = 8  # zscore斜率的窗口大小
    g.biasN = 90  # 乖离动量的时间天数
    g.lossN = 20  # 止损MA20的周期
    g.lossFactor = 1.005  # 止损比例
    g.SwitchFactor = 1.04  # 换仓位的比例
    g.Motion_1diff = 19  # 动量变化速度阈值
    g.raiser_thr = 4.8  # 股票前一天上涨比例阈值
    g.hold_stock = 'null'
    g.score_thr = -0.68  # RSRS标准分买入阈值
    g.score_fall_thr = -0.43  # RSRS标准分卖出阈值
    g.idex_slope_raise_thr = 12  # 大盘指数强势斜率阈值
    # 初始化斜率和RSRS标准分
    g.slope_series, g.rsrs_score_history = initial_slope_series()
    g.stock_motion = initial_stock_motion(g.stock_pool)  # 初始化动量因子
    # 定时运行函数
    run_daily(my_trade_prepare, time='7:00', reference_security='000300.XSHG')
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(my_sell2buy, time='9:35', reference_security='000300.XSHG')
    run_daily(check_lose, time='open', reference_security='000300.XSHG')
    run_daily(pre_hold_check, time='11:25')
    run_daily(hold_check, time='11:27')
```

**说明** ：

  * 初始化函数设定了策略的全局参数，包括股票池、动量计算天数、斜率计算天数、止损比例等。通过run_daily函数设定了策略的运行时间节点。

## 2. 斜率和动量初始化函数

**函数名：initial_slope_series**

```python
def initial_slope_series():
    length = g.N + g.M + g.K
    data = attribute_history(g.ref_stock, length, '1d', ['high', 'low', 'close'])
    multe_data = [get_ols(data.low[i:i+g.N], data.high[i:i+g.N]) for i in range(length - g.N)]
    slopes = [i[1] for i in multe_data]
    r2s = [i[2] for i in multe_data]
    zscores = [(get_zscore(slopes[i+1:i+1+g.M]) * r2s[i+g.M]) for i in range(g.K)]
    return slopes, zscores
```

**说明** ：

  * 该函数用于初始化斜率和RSRS标准分的时间序列，以便在策略运行时进行动态更新。

**函数名：initial_stock_motion**

```python
def initial_stock_motion(stock_pool):
    stock_motion = {}
    for stock in stock_pool:
        motion_que = []
        data = attribute_history(stock, g.biasN + g.momentum_day + 1, '1d', ['close'])
        data = data[:-1]
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000
        motion_que.append(score)
        stock_motion[stock] = motion_que
    return stock_motion
```

**说明** ：

  * 初始化股票的动量因子，作为择时策略的重要依据。

## 3. 持仓检查与止损逻辑

**函数名：pre_hold_check**

```python
def pre_hold_check(context):
    if context.portfolio.positions:
        for stk in context.portfolio.positions:
            dt = attribute_history(stk, g.lossN + 2, '60m', ['close'])
            dt['man'] = dt.close / dt.close.rolling(g.lossN).mean()
            if dt.man[-1] < 1.0:
                log.info("盘中可能止损，卖出：{}".format(stk))
                send_message("盘中可能止损，卖出：{}".format(stk))
```

**说明** ：

  * 检查持仓股票的盘中动态，若价格跌破均线则触发止损。

## 4. 动量因子计算

**函数名：get_rank**

```python
def get_rank(context, stock_pool):
    rank = []
    for stock in stock_pool:
        data = attribute_history(stock, g.biasN + g.momentum_day, '1d', ['close'])
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000
        adr = 100 * (data.close[-1] - data.close[-2]) / data.close[-2]
        rank.append([stock, score, adr])
        g.stock_motion[stock].append(score)
        if len(g.stock_motion[stock]) > 5:
            g.stock_motion[stock].pop(0)
    rank = [i for i in rank if not math.isnan(i[1])]
    rank.sort(key=lambda x: x[1], reverse=True)
    return rank[0]
```

**说明** ：

  * 该函数用于计算每只股票的动量因子，并根据因子值排序选出最优标的。

## 5. 交易策略

**函数名：my_trade_prepare**

```python
def my_trade_prepare(context):
    g.check_out_list = get_rank(context, g.stock_pool)
    g.timing_signal = get_timing_signal(context, g.ref_stock)
    log.info('今日自选及择时信号:{} {}'.format(g.check_out_list[0], g.timing_signal))
    cur_stock = g.check_out_list[0]
    cur_adr = g.check_out_list[2]
    change_rate = g.stock_motion[cur_stock][-1] - g.stock_motion[cur_stock][-2]
    if change_rate > g.Motion_1diff or cur_adr > g.raiser_thr:
        g.timing_signal = 'SELL'
        log.info("由于涨跌:{}%, 动量变化:{}，今日空仓".format(cur_adr, change_rate))
```

**说明** ：

  * my_trade_prepare 函数在开盘前根据动量因子和择时信号确定当日的交易方向。

**函数名：my_trade**

```python
def my_trade(context):
    if g.timing_signal == 'SELL':
        for stock in context.portfolio.positions:
            position = context.portfolio.positions[stock]
            close_position(position)
    elif g.timing_signal == 'BUY' or g.timing_signal == 'KEEP':
        adjust_position(context, g.check_out_list)
```

**说明** ：

  * my_trade 函数根据择时信号执行实际交易操作，包括买入、卖出或保持持仓。

## 6. 其他辅助函数

**斜率回归与因子计算函数** ：

```python
def get_ols(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (sum((y - (slope * x + intercept))**2) /
 ((len(y) - 1) * np.var(y, ddof=1)))
    return intercept, slope, r2
def get_zscore(slope_series):
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std
def get_zscore_slope(z_scores):
    y = z_scores
    x = np.arange(len(z_scores))
    slope, intercept = np.polyfit(x, y, 1)
    return slope
```

**说明** ：

  * 这些函数用于计算斜率、标准分等因子，是策略中择时逻辑的核心。

### 适用场景

本策略适用于希望在市场波动中寻找最佳投资机会，并通过技术分析和量化因子进行择时和调仓的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
