# 98、RSRS动量择时交易策略

# 策略概述

**RSRS动量择时交易策略** 是一种结合动量因子和RSRS择时模型的策略。该策略通过选择市场上动量最强的ETF基金进行投资，并结合RSRS标准分模型进行择时，优化交易决策，提升策略的风险调整收益。RSRS（Running Standard Regression Slope）是一种通过计算标准回归斜率并结合拟合度进行择时的模型，可帮助投资者在市场趋势形成时及时介入，在趋势反转时及时退出。

# 策略详细介绍

  1. **策略思想** ：

     * **动量选股** ：使用卡尔曼滤波对过去一段时间内的价格进行平滑，选择动量最大的ETF进行投资。

     * **RSRS择时** ：通过标准回归斜率的标准化分数和拟合度对市场进行择时判断，决定是否进行买入、持有或清仓操作。

  2. **策略代码与功能说明**

1\. 初始化函数 (initialize)

```python
def initialize(context):
    set_benchmark('399006.XSHE')  # 设定基准指数
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 避免引入未来信息
    set_slippage(FixedSlippage(0.001))  # 设置固定滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='fund')
    log.set_level('order', 'error')  # 设置日志级别
    g.stock_pool = [
        '510050.XSHG', # 上证50ETF
        '159928.XSHE', # 中证消费ETF
        '510300.XSHG', # 沪深300ETF
        '159949.XSHE', # 创业板500ETF
    ]
    g.stock_num = 1  # 只买入评分最高的1只股票
    g.momentum_day = 20  # 动量计算的时间窗口
    g.ref_stock = '000300.XSHG'  # 用于择时的参考指数
    g.N = 18  # RSRS模型计算窗口
    g.M = 600  # RSRS标准分计算窗口
    g.score_threshold = 0.7  # RSRS择时信号阈值
    g.slope_series = initial_slope_series()[:-1]  # 初始化斜率序列
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(check_lose, time='open', reference_security='000300.XSHG')
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')
```

  * **功能说明** : 初始化策略，包括设定交易参数、标的池、动量计算窗口、RSRS择时模型参数，并定义每日运行的交易函数。

  * **关键逻辑** : 初始化全局变量和策略环境，为后续策略逻辑的执行奠定基础。

2\. 卡尔曼滤波 (kalman_filter)

```python
def kalman_filter(observations, damping=1):
    observation_covariance = damping
    initial_value_guess = observations[0]
    transition_matrix = 1
    transition_covariance = 0.1
    kf = KalmanFilter(
        initial_state_mean=initial_value_guess,
        initial_state_covariance=observation_covariance,
        transition_matrices=transition_matrix,
        observation_covariance=observation_covariance,
        transition_covariance=transition_covariance,
    )
    pre, cov = kf.smooth(observations)
    return pre
```

  * **功能说明** : 使用卡尔曼滤波对历史价格数据进行平滑处理，以消除噪音并获取更平滑的价格趋势。

  * **关键逻辑** : 通过平滑处理，使得动量计算更加稳定，减少价格波动带来的干扰。

3\. 动量选股 (get_rank)

```python
def get_rank(context, stock_pool):
    rank = []
    for stock in g.stock_pool:
        data = attribute_history(stock, g.momentum_day, '1d', ['close'])
        data.close = data.close / data.close[0]
        pred_data = kalman_filter(np.array(data.close), 0.15)
        score = np.polyfit(np.arange(20), pred_data[-20:], 1)[0]
        rank.append([stock, score])
    rank.sort(key=lambda x: x[-1], reverse=True)
    return rank[0]
```

  * **功能说明** : 计算各ETF的20日动量，并根据动量得分对ETF进行排序，选择动量最大的ETF作为投资标的。

  * **关键逻辑** : 动量策略通过选择动量最大的ETF来捕捉市场的强势趋势，以获取更高的收益。

4\. RSRS择时信号 (get_timing_signal)

```python
def get_timing_signal(context, stock):
    data = attribute_history(g.ref_stock, 18, '1d', ['high', 'low'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    log.info('rsrs_score {:.3f}'.format(rsrs_score))
    if rsrs_score > g.score_threshold: return "BUY"
    elif rsrs_score < -g.score_threshold: return "SELL"
    else: return "KEEP"
```

  * **功能说明** : 根据RSRS模型的标准分和拟合度，生成买入、卖出或继续持有的信号。

  * **关键逻辑** : RSRS模型结合市场波动性和趋势，通过信号判断市场的多空状态，优化买卖决策。

5\. 交易主函数 (my_trade)

```python
def my_trade(context):
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    if hour == 9 and minute == 30:
        check_out_list = get_rank(context, g.stock_pool)
        timing_signal = get_timing_signal(context, g.ref_stock)
        print('今日自选及择时信号:{} {}'.format(check_out_list, timing_signal))
        if timing_signal == 'SELL':
            for stock in context.portfolio.positions:
                position = context.portfolio.positions[stock]
                close_position(position)
        elif timing_signal == 'BUY' or timing_signal == 'KEEP':
            adjust_position(context, check_out_list)
```

  * **功能说明** : 每日交易逻辑，根据动量选股结果和RSRS择时信号，进行买入、持有或清仓操作。

  * **关键逻辑** : 结合动量选股和RSRS择时，最大化捕捉市场趋势，同时控制回撤风险。

6\. 辅助函数 (adjust_position, check_lose, print_trade_info)

```python
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            log.info("[%s]已不在应买入列表中" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("[%s]已经持有无需重复买入" % (stock))
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                open_position(stock, value)
                if len(context.portfolio.positions) == g.stock_num:
                    break
def check_lose(context):
    for position in list(context.portfolio.positions.values()):
        if 100 * (position.price / position.avg_cost - 1) <= -90:
            order_target_value(position.security, 0)
            log.info("止损: 标的={}, 浮动盈亏={}%".format(position.security, format(ret, '.2f')))
def print_trade_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
```

  * **功能说明** : 辅助函数用于持仓调整、止损检查以及打印每日的交易信息，帮助策略保持高效的执行和风险控制。

  * **关键逻辑** : 通过持仓调整和止损机制，控制风险，确保策略在市场逆风时的回撤控制。

### 总结

**RSRS动量择时交易策略** 通过结合动量选股和RSRS择时模型，在市场上寻找最强势的ETF进行投资，并在市场趋势明确时入场，在趋势逆转时退出。该策略在有效捕捉市场趋势的同时，通过RSRS模型来优化择时决策，降低回撤，提升收益的稳定性。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
