# 88、RSRS择时与多因子选股策略

# 策略概述

**RSRS择时与多因子选股策略** 是一个结合了RSRS（回归标准分数）择时模型和多因子选股模型的量化投资策略。该策略通过RSRS模型对市场趋势进行判断，并结合多因子选股筛选出优质股票。策略在市场趋势向好的情况下进行持仓，在趋势转坏时清仓，旨在通过市场趋势和基本面因素的结合，获取稳健的超额收益。

# 策略详细介绍

  1. **策略思想** ：

     * **RSRS择时模型** ：使用RSRS模型（基于高低价的回归标准分数）判断市场的整体趋势，在趋势向好时买入股票，在趋势向坏时卖出股票。

     * **多因子选股模型** ：利用多个财务因子筛选出成长性较好的股票，通过过滤停牌、ST、涨跌停等条件，挑选出风险较低的优质股票进行投资。

     * **动态调仓** ：策略根据择时信号决定是否调整持仓，同时每次调整时均衡分配资金，确保组合的风险分散。

  2. **关键要素** ：

     * **RSRS择时** ：根据沪深300指数的历史高低价数据计算RSRS指标，并根据标准分数判断市场趋势。

     * **多因子选股** ：结合多个财务因子，如净利润增长率、PEG等，筛选出基本面优质的股票。

     * **风险控制** ：通过定期调仓和择时策略相结合，控制投资组合的整体风险。

# 策略代码与功能说明

1\. 初始化函数与全局变量设置 (initialize)

```python
def initialize(context):
    set_benchmark('399300.XSHE')  # 基准为沪深300指数
    set_option('use_real_price', True)  # 用真实价格交易
    set_option("avoid_future_data", True)  # 防止未来函数
    set_slippage(FixedSlippage(0))  # 设置固定滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5),type='fund')
    log.set_level('order', 'error')  # 只记录error级别以上的日志
    g.stock_num = 4  # 每次持仓的股票数量
    g.ref_stock = '000300.XSHG'  # 择时的基准股票（沪深300）
    g.N = 18  # 计算RSRS斜率的天数
    g.M = 600  # 计算RSRS标准分数的天数
    g.score_threshold = 0.7  # RSRS标准分数的阈值
    g.mean_day = 30  # 移动平均线的天数
    g.mean_diff_day = 2  # 移动平均线偏差天数
    g.slope_series = initial_slope_series()[:-1]  # 初始化斜率序列
    run_daily(my_trade, time='9:45', reference_security='000300.XSHG')  # 每日交易时间
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')  # 每日收盘后打印信息
```

  * **功能说明** : 初始化策略参数，包括基准设置、交易费用、滑点等。并设置每日的交易时间和收盘后打印信息。

  * **关键逻辑** :

    * g.ref_stock 用于择时的基准股票（沪深300）。

    * g.slope_series 初始化用于计算RSRS指标的斜率序列。

2\. 多因子选股模块 (get_factor_filter_list, get_stock_list)

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame(columns=['code', 'score'])
    df['code'] = stock_list
    df['score'] = score_list
    df = df.dropna()
    df = df[df['score'] > 0]
    df.sort_values(by='score', ascending=sort, inplace=True)
    filter_list = list(df.code)[0:int(p * len(stock_list))]
    return filter_list
def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    profit_growth_list = get_factor_filter_list(context, initial_list, 'net_profit_growth_rate', False, 0.1)
    peg_list = get_factor_filter_list(context, profit_growth_list, 'PEG', True, 0.5)
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(peg_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    final_list = list(df.code)
    return final_list
```

  * **功能说明** : 根据多因子模型筛选股票，包括净利润增长率和PEG等因子，并按市值排序后选择最终股票列表。

  * **关键逻辑** :

    * get_factor_filter_list 按因子值排序并筛选出前一定比例的股票。

    * get_stock_list 返回经过多因子筛选和过滤后的股票列表。

3\. 交易模块 (order_target_value_, open_position, close_position, adjust_position, my_trade)

```python
def order_target_value_(security, value):
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if open_position(stock, value) and len(context.portfolio.positions) == g.stock_num:
                break
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
```

  * **功能说明** : 根据RSRS择时信号和多因子选股结果调整持仓，进行买入或卖出操作。

  * **关键逻辑** :

    * get_timing_signal 通过RSRS择时模型判断当前市场趋势，决定是买入、持有还是卖出。

    * adjust_position 依据择时信号和选股结果，调整持仓至目标股票列表。

4\. 复盘与信息打印模块 (print_trade_info)

```python
def print_trade_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：'+str(_trade))
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price/cost - 1)
        value = position.value
        amount = position.total_amount
        print('代码:{}'.format(securities))
        print('成本价:{}'.format(format(cost,'.2f')))
        print('现价:{}'.format(price))
        print('收益率:{}%'.format(format(ret,'.2f')))
        print('持仓(股):{}'.format(amount))
        print('市值:{}'.format(format(value,'.2f')))
        print('———————————————————————————————————')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
```

  * **功能说明** : 打印每日持仓和交易信息，便于复盘和策略评估。

  * **关键逻辑** :

    * 打印交易记录、持仓股票的收益率及市值等详细信息

。

策略总结

**RSRS择时与多因子选股策略** 通过结合RSRS择时模型和多因子选股模型，动态调整持仓，力求在市场趋势向好的时候最大化收益，并在趋势转坏时及时撤出，避免损失。策略兼顾了择时与选股两个维度，能够在不同市场环境中有效运作，适合追求稳健回报的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
