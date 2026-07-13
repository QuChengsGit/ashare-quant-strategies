# 66、指数增强择时与SVR选股策略

### 策略介绍

**指数增强择时与SVR选股策略** 是一种结合了指数择时和机器学习选股的量化交易策略。该策略通过RSRS（相对强弱斜率）指标对市场进行择时判断，并结合支持向量回归（SVR）模型进行股票选择，旨在捕捉市场中的相对收益。策略不仅关注大盘趋势，还通过行业、基本面等多因素分析选出最优股票组合，在合适的时机买入和卖出，力求实现超额收益。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
from jqdata import *
import numpy as np
from sklearn.svm import SVR
import pandas as pd
def initialize(context):
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')
    set_benchmark('000300.XSHG')  # 设置沪深300为基准
    g.stock_num = 10  # 目标持仓股票数量
    g.curstaut = 0  # 0 表示当前空仓，1 表示满仓
    g.ref_stock = '000001.XSHG'  # 选取上证指数作为参考指数
    g.N = 18  # 计算斜率和拟合度参考的天数
    g.M = 600  # 计算标准分zscore参考的天数
    g.K = 8  # 计算 zscore 斜率的窗口大小
    g.score_thr = -1  # RSRS标准分的买入阈值
    g.score_fall_thr = -0.5  # RSRS标准分的卖出阈值
    g.idex_slope_raise_thr = 10  # 指数斜率上升判断标准
    g.slope_series, g.rsrs_score_history = initial_slope_series()  # 初始化斜率和RSRS评分历史
    run_daily(my_trade_prepare, time='9:00', reference_security='000300.XSHG')
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
```

技术说明：

  * **初始化函数** ：设置策略的基本配置，包括交易成本、基准指数和择时策略的相关参数。策略通过两个每日运行的函数来实现择时和交易。

2\. 斜率计算与择时逻辑

```python
def initial_slope_series():
    length = g.N + g.M + g.K
    data = attribute_history(g.ref_stock, length, '1d', ['high', 'low', 'close'])
    multe_data = [get_ols(data.low[i:i + g.N], data.high[i:i + g.N]) for i in range(length - g.N)]
    slopes = [i[1] for i in multe_data]
    r2s = [i[2] for i in multe_data]
    zscores = [(get_zscore(slopes[i + 1:i + 1 + g.M]) * r2s[i + g.M]) for i in range(g.K)]
    return slopes, zscores
def get_ols(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
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
def get_timing_signal(context, stock):
    data = attribute_history(g.ref_stock, g.N, '1d', ['high', 'low', 'close'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    g.rsrs_score_history.append(rsrs_score)
    rsrs_slope = get_zscore_slope(g.rsrs_score_history[-g.K:])
    idex_slope = np.polyfit(np.arange(8), data.close[-8:], 1)[0].real
    g.slope_series.pop(0)
    g.rsrs_score_history.pop(0)
    log.info(f'rsrs_slope: {rsrs_slope:.3f}, rsrs_score: {rsrs_score:.3f}, idex_slope: {idex_slope:.3f}')
    if rsrs_slope < 0 and rsrs_score > 0:
        return "SELL"
    if idex_slope < 0 and rsrs_slope > 0 and rsrs_score < g.score_fall_thr:
        return "SELL"
    if idex_slope > g.idex_slope_raise_thr and rsrs_slope > 0:
        return "BUY"
    if rsrs_score > g.score_thr:
        return "BUY"
    return "SELL"
```

技术说明：

  * **斜率和RSRS指标** ：通过对高低价进行线性回归，计算出斜率、拟合度，并通过标准化后的RSRS指标来判断市场趋势。

  * **择时信号** ：根据RSRS指标的斜率和分值来确定买卖信号，同时考虑了大盘指数的趋势。

3\. 交易模块与调仓逻辑

```python
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
            g.hold_stock = 'null'
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        g.hold_stock = stock
                        break
def open_position(security, value):
    order = order_target_value(security, value)
    if order is not None and order.filled > 0:
        return True
    return False
def close_position(position):
    security = position.security
    order = order_target_value(security, 0)
    if order is not None and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False
```

技术说明：

  * **持仓调整** ：根据择时信号调整持仓，通过买入评分最高的股票并平仓不符合条件的股票，实现资金的动态配置。

  * **买卖决策** ：通过开放和平仓函数实现自动交易，根据择时信号判断是否需要调整仓位。

4\. 选股策略与支持向量回归（SVR）

```python
def today_prepare(context):
    n_position = g.stock_num
    n_choice = int(1.2 * n_position)
    cdata = get_current_data()
    dt_last = context.previous_date
    index_list = ['399101.XSHE']  # 中小板综指
    stocks = _get_stocks(index_list, dt_last)
    q = query(
            valuation.code,
            valuation.market_cap,
            valuation.pb_ratio > 0,
            indicator.inc_return > 0,
            indicator.inc_total_revenue_year_on_year > 0,
            indicator.inc_net_profit_year_on_year > 0,
            indicator.ocf_to_operating_profit > 5,
        ).filter(
            valuation.code.in_(stocks),
            balance.total_assets > balance.total_liability,
            income.net_profit > 0,
        )
    df = get_fundamentals(q, dt_last).fillna(0).set_index('code')
    df.columns = ['log_mc', 'log_NC', 'log_NI', 'log_RD', 'PE', 'OCF']
    svr = SVR(kernel='rbf')
    Y = df['log_mc']
    X = df.drop('log_mc', axis=1)
    model = svr.fit(X, Y)
    r = Y - pd.Series(svr.predict(X), Y.index)
    r = r[r < 0].sort_values().head(n_choice)
    choice = r.index.tolist()
    if g.curstaut == 0:
        if g.timing_signal == "BUY":
            g.check_out_list = choice
            g.curstaut = 1
        else:
            g.check_out_list = []
    else:
        if g.timing_signal == "SELL":
            g.check_out_list = []
            g.curstaut =
 0
        else:
            g.check_out_list = choice
```

技术说明：

  * **选股逻辑** ：通过支持向量回归（SVR）模型对股票的多种因子进行分析，选择符合条件的股票进行投资。选股时考虑了市值、盈利能力和现金流等多种因素。

  * **调仓逻辑** ：根据当日的择时信号和SVR选股结果，确定最终的交易名单。

### 策略优势

  * **指数增强择时** ：利用RSRS指标对市场趋势进行判断，有效规避市场下行风险，捕捉市场上行机会。

  * **机器学习选股** ：采用支持向量回归模型，结合多因子分析，确保选出的股票具有较高的投资价值。

  * **动态调整** ：根据市场和个股的变化，实时调整持仓，确保策略的灵活性和应对市场变化的能力。

### 总结

**指数增强择时与SVR选股策略** 通过结合指数择时和机器学习选股，为投资者提供了一种基于量化模型的策略，旨在提高市场中的相对收益。策略逻辑清晰，能够在一定程度上控制风险并抓住市场机会，适用于追求稳健收益的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
