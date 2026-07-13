# 44、多因子动量择时与多维度选股策略

# 1. 策略概述

本策略结合多因子选股和动量择时机制，旨在筛选出质量较高、具备增长潜力的股票，并通过动量因子判断大盘趋势，在适当的时机进行买卖操作。通过多维度的过滤和因子评分，策略在不同的市场环境下动态调整持仓，以期获得稳定的超额收益。

# 2. 策略各部分功能代码详细技术文档说明

## 2.1 策略初始化 (initialize)

策略初始化时，设置了交易的基本参数，包括基准指数、滑点、交易成本等。同时，定义了关键的全局变量，如持仓数量、择时计算参数、选股权重等。策略通过run_daily定期执行交易和调仓操作。

```python
def initialize(context):
    set_benchmark('399101.XSHE')  # 设定中证创新100指数为基准
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来函数
    set_slippage(FixedSlippage(0))  # 设置滑点为0，假设无滑点影响
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    # 选股参数
    g.stock_num = 4  # 最大持仓股票数
    g.ref_stock = '000300.XSHG'  # 用于择时的大盘指数
    g.N = 18  # 动量择时计算的天数
    g.M = 600  # 动量择时中RSRS指标的窗口长度
    g.score_threshold = 0.7  # 动量择时的RSRS得分阈值
    g.mean_day = 30  # 移动平均线天数
    g.mean_diff_day = 2  # 移动平均线计算的额外天数
    g.slope_series = initial_slope_series()[:-1]  # 动量择时斜率序列初始化
    g.weights = [3, 9, 8, 4, 10]  # 选股因子的权重设置
    g.sellrank = 10  # 排名超过此值的股票将被卖出
    g.buyrank = 9  # 排名在此值以内的股票可以买入
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')
```

## 2.2 多因子选股模块 (get_stock_list)

该模块通过多个财务因子和技术因子筛选股票，包括PEG、净利润增长率、成交金额的标准差等。最后通过因子权重的加权计算，得到综合评分最高的股票列表。

```python
def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = growth_profit(context, initial_list)  # 净利润增长率筛选
    initial_list = peg(context, initial_list)  # PEG筛选
    initial_list = get_factor_filter_list(context, initial_list, 'TVSTD20', True, 0, 0.3)  # 20日成交金额的标准差筛选
    final_list = get_stock_rank_m_m(context, initial_list)  # 综合因子评分筛选
    return final_list
```

## 2.3 过滤模块

过滤模块包括多个函数，用于过滤掉不符合条件的股票，如停牌、ST、涨停、跌停、科创板、次新股等。每个函数根据特定的条件筛选股票，并返回符合条件的股票列表。

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < current_data[stock].high_limit]
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [stock for stock in stock_list if not yesterday - get_security_info(stock).start_date < datetime.timedelta(days=250)]
```

## 2.4 动量择时模块 (get_timing_signal)

该模块使用RSRS因子来判断市场的动量趋势，通过计算大盘的高低点线性回归斜率并进行标准化，判断市场是否处于买入、持有或卖出的状态。

```python
def get_timing_signal(context, stock):
    g.mean_diff_day = 5
    close_data = attribute_history(g.ref_stock, g.mean_day + g.mean_diff_day, '1d', ['close'])
    high_low_data = attribute_history(g.ref_stock, g.N, '1d', ['high', 'low'])
    intercept, slope, r2 = get_ols(high_low_data.low, high_low_data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    if rsrs_score > g.score_threshold: return "BUY"
    elif rsrs_score < -g.score_threshold: return "SELL"
    else: return "KEEP"
```

## 2.5 交易模块 (my_trade)

交易模块结合择时信号和选股结果进行买卖操作。若择时信号为“SELL”，则平仓所有股票；若为“BUY”或“KEEP”，则根据选股结果进行调仓操作。

```python
def my_trade(context):
    check_out_list = get_stock_list(context)
    check_out_list = filter_limitup_stock(context, check_out_list)
    check_out_list = filter_limitdown_stock(context, check_out_list)
    check_out_list = filter_paused_stock(check_out_list)
    check_out_list = check_out_list[:g.stock_num]
    print('今日自选股:{}'.format(check_out_list))
    g.timing_signal = get_timing_signal(context, g.ref_stock)
    if g.timing_signal == 'SELL':
        for stock in context.portfolio.positions:
            position = context.portfolio.positions[stock]
            close_position(position)
    elif g.timing_signal == 'BUY' or g.timing_signal == 'KEEP':
        adjust_position(context, check_out_list)
    else: pass
```

## 2.6 辅助函数模块

辅助函数模块包含用于计算线性回归斜率、z-score标准化等功能的函数，为策略的其他部分提供支持。

```python
def get_ols(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return (intercept, slope, r2)
def initial_slope_series():
    data = attribute_history(g.ref_stock, g.N + g.M, '1d', ['high', 'low'])
    return [get_ols(data.low[i:i+g.N], data.high[i:i+g.N])[1] for i in range(g.M)]
def get_zscore(slope_series):
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std
```

# 3. 策略优化建议

  1. **参数优化** ：通过历史回测优化g.score_threshold、g.mean_day等参数，以获得更好的表现。

  2. **多因子融合** ：结合更多的因子（如市净率、动量等）进行选股，提升股票筛选的质量。

  3. **风险控制** ：引入最大回撤控制、波动率控制等风险管理措施，减少极端市场环境对策略的冲击。

  4. **分散投资** ：考虑同时持有多只不同权重的股票，以分散风险，提升整体策略的稳定性。

通过这套多因子选股和动量择时相结合的策略，投资者可以在市场中捕捉到优质股票的上涨机会，并在市场下行时及时止损，保护收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
