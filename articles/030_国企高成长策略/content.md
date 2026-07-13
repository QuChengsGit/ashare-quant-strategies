# 30、国企高成长策略

### 策略简介

“国企高成长策略”是一种专注于筛选具有高成长潜力的国有企业股票的量化交易策略。策略以国有企业股票为主要标的，通过多因子筛选和技术分析手段，构建优质持仓组合，并根据市场状况进行动态调整。策略特别关注股票的基本面表现和市场流动性，结合涨停板和风险控制机制，确保持仓的稳定性和收益的持续性。

### 策略结构与功能

### 1. 初始化函数

```python
def initialize(context):
    # 设定基准
    set_benchmark('000300.XSHG')  # 沪深300指数
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 设置滑点为0，适用于理论研究和回测
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003,
                            close_today_commission=0, min_commission=5), type='stock')
    # 日志配置
    log.set_level('order', 'error')
    log.set_level('system', 'error')
    # 初始化全局变量
    g.stock_num = 4  # 最大持仓数
    g.limit_up_list = []  # 记录持仓中涨停的股票
    g.hold_list = []  # 当前持仓的全部股票
    g.limit_days = 20  # 不再买入的时间段天数
    g.target_list = []  # 开盘前预操作股票池
    # 配置调度任务
    do_schedule(context)
```

  * **功能说明** :

    * 初始化策略的各项参数，包括基准设定、滑点、交易成本等。

    * 设置全局变量，并配置调度任务以确保策略按时执行。

### 2. 调度任务设置

```python
def do_schedule(context):
    # 设置交易运行时间
    run_daily(get_stock_list, time='8:00', reference_security='000300.XSHG')  # 选股
    run_daily(prepare_trade, time='8:05', reference_security='000300.XSHG')  # 准备交易
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 检查涨停
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一调仓
    run_weekly(print_position_info, weekday=1, time='15:10', reference_security='000300.XSHG')  # 每周一打印持仓信息
```

  * **功能说明** :

    * 定义策略各模块的运行时间和频率，确保调度的合理性和有效性。

### 3. 选股模块

```python
def get_stock_list(context):
    yesterday = context.previous_date
    # 定义国企股票列表
    stocklists = [
        '601919.XSHG', '300073.XSHE', '600536.XSHG', '000951.XSHE',
        '601628.XSHG', '600036.XSHG', '601818.XSHG', '001289.XSHE',
        ...
        '600029.XSHG', '002916.XSHE', '301269.XSHE', '600482.XSHG'
    ]
    stocklists = filter_st_stock(stocklists)  # 过滤ST股
    # 根据预期增长率剔除后15%的股票
    factor_data = get_factor_values(securities=stocklists, factors=['growth'], end_date=yesterday, count=1)['growth'].iloc[0]
    growth_list = factor_data.sort_values(ascending=False).index.tolist()
    growth_list = growth_list[:int(len(growth_list) * 0.80)]
    # 根据PE和PB复合排序并考虑行业比重
    df = get_valuation(growth_list, end_date=yesterday, fields=['pe_ratio', 'pb_ratio'], count=1).set_index('code')
    df['sw_code'] = ''
    industry_data = get_industry(security=growth_list, date=context.previous_date)
    for stock in growth_list:
        df.loc[stock, 'sw_code'] = industry_data[stock].get('sw_l1')['industry_code']
    # 筛选特定行业股票并计算综合评分
    df = df[df['sw_code'].isin(['801180', '801780', '801790', '801720'])]
    df['dense'] = df.groupby('sw_code')['pb_ratio'].rank(method='min', ascending=True, pct=True)
    df['score'] = df['dense'] * 0.8 + df.pe_ratio.rank(method='min', ascending=True, pct=True) * 0.2
    # 按评分排序并选择前N只股票作为目标股票池
    pb_list = df.sort_values('score', ascending=True).index.tolist()
    g.target_list = pb_list[:g.stock_num + 2]  # 多选2只以备不时之需
    return g.target_list
```

  * **功能说明** :

    * 通过筛选符合条件的国有企业股票，考虑成长性、估值水平（PE、PB）及行业比重，构建目标股票池。

### 4. 准备交易和调仓

```python
def prepare_trade(context):
    g.hold_list = list(context.portfolio.positions.keys())
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)
```

  * **功能说明** :

    * 在开盘前准备持仓和昨日涨停股的信息，以便后续操作中进行精准调整。

```python
def weekly_adjustment(context):
    g.target_list = filter_paused_stock(g.target_list)
    g.target_list = filter_limitup_stock(context, g.target_list)
    g.target_list = filter_limitdown_stock(context, g.target_list)
    black_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)
    g.target_list = [stock for stock in g.target_list if stock not in black_list]
    # 卖出不符合条件的股票
    for stock in g.hold_list:
        if stock not in g.target_list and stock not in g.high_limit_list:
            close_position(stock)
    # 买入新的股票
    position_count = len(context.portfolio.positions)
    if position_count < g.stock_num:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in g.target_list:
            if stock not in context.portfolio.positions.keys():
                if open_position(stock, value):
                    if len(context.portfolio.positions) >= g.stock_num:
                        break
```
  * **功能说明** :

    * 每周一调整持仓，根据筛选出的目标股票池动态调仓，确保持仓股票符合策略要求。

### 5. 涨停股检查

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'],
                                     skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                log.info("[%s]涨停打开，卖出" % (stock))
                close_position(stock)
            else:
                log.info("[%s]涨停，继续持有" % (stock))
```

  * **功能说明** :

    * 每天下午检查昨日涨停股票，如果发现涨停打开，则卖出以防止回调风险。

### 6. 辅助函数与工具

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st]
def get_recent_limit_up_stock(context, stock_list, recent_days):
    stat_date = context.previous_date
    return get_price(stock_list, end_date=stat_date, frequency='daily', fields=['close', 'high_limit'],
                     count=recent_days, panel=False, fill_paused=False).query('close==high_limit').code.tolist()
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[
stock][-1] < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[stock][-1] > current_data[stock].low_limit]
def close_position(position):
    order = order_target_value(position, 0)
    if order is not None and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False
```

  * **功能说明** :

    * 这些函数用于过滤股票池中不符合条件的股票，如停牌、ST、涨跌停等，确保策略操作的严谨性和有效性。



### 总结

国企高成长策略是一种基于基本面和技术面的量化交易策略，专注于筛选高成长潜力的国有企业股票。策略通过多因子筛选、动态调仓和严格的风控机制，力求在市场中实现稳健的收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
