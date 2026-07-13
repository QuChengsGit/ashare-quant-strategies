# 29、高成长因子动态调整策略

### 策略简介

“高成长因子动态调整策略”是一种基于基本面和技术面综合筛选的量化交易策略。策略通过筛选高成长性股票并结合多种市场信号，动态调整持仓。该策略不仅关注个股的财务健康和成长性，还结合了市场情绪（如涨停信息）进行灵活的买卖操作。同时，通过历史持仓数据和防范追涨杀跌，避免过度频繁交易，提高策略的稳健性。

### 策略结构与功能

### 1. 初始化函数

```python
def initialize(context):
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 防止未来数据泄露
    log.set_level('order', 'error')  # 设置日志级别为error
    # 设置滑点和交易成本
    set_slippage(FixedSlippage(0.02))
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0002, close_commission=0.0002, min_commission=0.01), type='stock')
    # 全局变量初始化
    g.total_stock_num = 10  # 最大持仓数量
    g.hold_list = []  # 当前持仓股票列表
    g.buy_list = []  # 需要买入的股票列表
    g.high_limit_list = []  # 昨日涨停的持仓股票
    g.limit_up_list = []  # 涨停的持仓股票
    g.history_hold_list = []  # 过去一段时间内的持仓股票列表
    g.not_buy_again_list = []  # 最近买过且涨停的股票列表
    g.limit_days = 20  # 不再买入的时间段天数
    g.is_empty_position = False  # 是否空仓信号
    # 定时任务设置
    run_daily(before_market_open, time='09:25', reference_security='000300.XSHG')
    run_weekly(market_opened, weekday=1, time='09:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:40', reference_security='000300.XSHG')
    run_daily(clear_account, '14:50')
```

  * **功能说明** :

    * 初始化策略各项参数和设置，包括全局变量的初始化。

    * 设定定时任务，确保策略按计划运行。

### 2. 开盘前函数

```python
def before_market_open(context):
    g.is_empty_position = today_is_between(context, '04-01', '04-30')  # 判断4月空仓信号
    get_history_hold_list(context)  # 获取历史持仓列表
    get_yesterday_limit_up_stocks(context)  # 获取昨日涨停列表
```

  * **功能说明** :

    * 判断是否处于4月空仓期，并获取历史持仓和昨日涨停股票，准备当天的交易。

### 3. 调仓函数

```python
def market_opened(context):
    if g.is_empty_position == False:
        adjustment(context, context.previous_date)
``` ```python
def adjustment(context, yesterday):
    all_stocks = list(get_all_securities(types=['stock'], date=yesterday).index)
    g.buy_list = basic_filters(context, all_stocks)  # 基础过滤
    g.buy_list = get_high_growth_stocks(context, g.buy_list)[:g.total_stock_num * 2]  # 获取高增长股票池
    recent_limit_up_list = get_recent_limit_up_stock(context, g.buy_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    g.buy_list = [stock for stock in g.buy_list if stock not in black_list]  # 过滤黑名单中的股票
    g.buy_list = filter_limitup_stock(context, g.buy_list)[:min(g.total_stock_num, len(g.buy_list))]  # 过滤涨停股票
    # 卖出不在买入列表中的股票
    for stock in context.portfolio.positions:
        if stock not in g.buy_list and stock not in g.high_limit_list:
            limit_price = get_current_data()[stock].last_price * 0.9
            order_target(stock, 0, MarketOrderStyle(limit_price))
            log.info("日常调仓卖出[%s]" % (stock))
    # 购买新的股票
    no_hold_target_num = g.total_stock_num - len(context.portfolio.positions)
    if no_hold_target_num > 0:
        cash_per_stock = context.portfolio.available_cash / no_hold_target_num
        for stock in g.buy_list:
            if stock not in g.hold_list:
                limit_price = get_current_data()[stock].last_price * 1.1
                order_target_value(stock, cash_per_stock, MarketOrderStyle(limit_price))
```

  * **功能说明** :

    * 筛选符合策略要求的股票并进行调仓操作，卖出不在买入列表中的股票，按预设比例买入新股票。

### 4. 高增长股票筛选函数

```python
def get_high_growth_stocks(context, stock_codes):
    yesterday = context.previous_date
    q = query(
        income.code,
        income.operating_revenue,
        indicator.adjusted_profit,
        valuation.pe_ratio,
        valuation.market_cap
    ).filter(
        income.code.in_(stock_codes),
        valuation.pe_ratio <= 30,
        valuation.pe_ratio > 0,
        indicator.adjusted_profit > 0,
    )
    now_df = get_fundamentals(q, date=yesterday)
    lastyear_same_day = datetime.date(yesterday.year - 1, yesterday.month, yesterday.day)
    lastyear_q = query(
        income.code,
        income.operating_revenue,
        indicator.adjusted_profit,
        valuation.pe_ratio
    ).filter(
        income.code.in_(now_df['code'].values.tolist())
    )
    lastyear_df = get_fundamentals(lastyear_q, date=lastyear_same_day)
    merged_df = pd.merge(now_df, lastyear_df, on='code', suffixes=['', '_lastyear'])
    merged_df['growth_operating_revenue'] = (merged_df['operating_revenue'] - merged_df['operating_revenue_lastyear']) / abs(merged_df['operating_revenue_lastyear'])
    merged_df['growth_adjusted_profit'] = (merged_df['adjusted_profit'] - merged_df['adjusted_profit_lastyear']) / abs(merged_df['adjusted_profit_lastyear'])
    merged_df['peg'] = merged_df['pe_ratio'] / (merged_df['growth_adjusted_profit'] * 100)
    df = merged_df.loc[(merged_df['peg'] <= 1) & (merged_df['growth_adjusted_profit'] > 0) & (merged_df['growth_operating_revenue'] >= 0.15), :]
    df = df.sort_values(by='market_cap')
    return list(df['code'])
```

  * **功能说明** :

    * 通过对比当前季度和去年同期的财务数据，筛选出营收和利润增长显著的股票，并根据市值进行排序，优选出具有高成长潜力的股票。

### 5. 涨停股票处理与基础过滤

```python
def get_recent_limit_up_stock(context, stock_list, recent_days):
    new_list = []
    for stock in stock_list:
        df = get_price(stock, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=recent_days, panel=False)
        if df[df['close'] == df['high_limit']].empty:
            new_list.append(stock)
    return new_list
def check_limit_up(context):
    for stock in g.high_limit_list:
        current_data = get_price(stock, end_date=context.current_dt, frequency='1m', fields=['close', 'high_limit'], count=1, panel=False)
        if current_data.iloc[0, 0] < current_data.iloc[0, 1] * 1.1:
            limit_price = current_data.iloc[0, 0] * 0.8
            order_target(stock, 0, MarketOrderStyle(limit_price))
            log.info("[%s]涨停打开，卖出" % (stock))
```

  * **功能说明** :

    * 筛选最近N天内涨停过的股票，并在尾盘检查涨停打开的股票，决定是否卖出以防止回调风险。

### 6. 基础过滤与清仓

```python
def basic_filters(context, stock_list):
    yesterday = context.previous_date
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
        current_data[stock].is_st or
        'ST' in current_data[stock].name or
        '*' in current_data[stock].name or
        '退' in current_data[stock].name or
        yesterday - get_security_info(stock).start_date <= datetime.timedelta(days=375) or
        current_data[stock].paused
    )]
def clear_account(context):
    if g.is_empty_position:
        for stock in context.portfolio.positions:
            limit
_price = get_current_data()[stock].last_price * 0.9
            order_target(stock, 0, MarketOrderStyle(limit_price))
```

  * **功能说明** :

    * 对股票进行基础的过滤操作，排除停牌、ST、次新股等风险股票，并在需要空仓时，清仓所有持仓股票。



### 总结

高成长因子动态调整策略是一种结合基本面和技术面双重筛选的稳健性量化策略。通过严格的选股和调仓规则，策略力求在市场中捕捉高增长、低估值的股票机会，同时通过动态调整仓位和严格的风控机制来规避市场的潜在风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
