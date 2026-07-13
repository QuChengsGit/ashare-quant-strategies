# 86、短期涨停板追踪与风险控制策略

# 策略概述

**短期涨停板追踪与风险控制策略** 是一种专注于捕捉涨停板股票的短期交易策略。该策略通过实时监控市场中的涨停板股票，利用集合竞价、开盘及盘中数据对目标股票进行筛选和风险控制。策略的核心在于捕捉高潜力的连续涨停股票，同时通过止损和择时机制控制风险，适用于高频短线交易者。

# 策略详细介绍

  1. **策略思想** ：

     * 策略主要捕捉连续涨停板的股票，通过集合竞价数据筛选出符合预期的目标股票。

     * 在开盘和盘中实时监控股票走势，执行买入、卖出决策，保证高收益同时控制下行风险。

     * 通过止损、止盈和市场条件分析，动态调整持仓，确保策略的稳健性。

  2. **关键要素** ：

     * **涨停板追踪** ：实时跟踪市场中的涨停股票，并筛选出具备进一步上涨潜力的股票。

     * **集合竞价筛选** ：使用集合竞价数据进行初步筛选，确认潜在的优质标的。

     * **盘中交易与风险控制** ：在开盘和盘中结合实时数据进行交易和风险管理。

     * **多层次的卖出策略** ：结合止损、止盈、尾盘策略，优化卖出时机。

# 策略代码与功能说明

1\. 初始化函数与全局变量设置 (initialize)

```python
def initialize(context):
    set_option("avoid_future_data", True)
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    log.info('初始函数开始运行且全局只运行一次')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 设置运行时间
    set_run_daily()
    # 待买列表
    g.buy_list=[]
```

  * **功能说明** : 初始化策略参数，包括基准、交易成本、每日运行的时间安排，以及待买入股票的全局列表。

  * **关键逻辑** :

    * set_benchmark 设置基准指数为沪深 300 指数（000300.XSHG）。

    * set_run_daily 设置每日多个时段的运行时间，如开盘前、盘中、收盘前等。

2\. 每日运行时间设定 (set_run_daily)

```python
def set_run_daily():
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(Call_auction, time='09:25', reference_security='000300.XSHG')
    run_daily(market_open_sell_buy, time='every_bar', reference_security='000300.XSHG')
    run_daily(before_closing, time='14:55', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
```

  * **功能说明** : 定义了每日不同时间点运行的函数，包括开盘前准备、开盘时的交易策略、盘中交易、收盘前清理及收盘后分析等。

  * **关键逻辑** :

    * run_daily 方法设置了各个时段执行的函数，比如 market_open 函数会在开盘时执行，after_market_close 函数会在收盘后执行。

3\. 开盘前运行函数 (before_market_open)

```python
def before_market_open(context):
    g.run_count=0
```

  * **功能说明** : 在开盘前运行，用于初始化每日的运行计数器。

  * **关键逻辑** :

    * g.run_count 用于记录盘中函数的运行次数，控制盘中交易的节奏。

4\. 集合竞价时运行函数 (Call_auction)

```python
def Call_auction(context):
    log.info('函数运行时间(Call_auction)：'+str(context.current_dt.time()))
    morning_observation(context)
```

  * **功能说明** : 在集合竞价期间（09:25）运行，用于观察集合竞价数据并初步筛选股票。

  * **关键逻辑** :

    * morning_observation 调用集合竞价观察函数，筛选早盘的强势股票。

5\. 盘中实时交易与风险管理 (market_open_sell_buy, clearn_every_bar)

```python
def market_open_sell_buy(context):
    inntraday_trading(context)
    clearn_every_bar(context)
    g.run_count+=1
    if g.run_count==240:
        g.run_count=0
def clearn_every_bar(context):
    curr_data=get_current_data()
    hour=context.current_dt.hour
    minute=context.current_dt.minute
    sells=list(context.portfolio.positions)
    for s in sells:
        if context.portfolio.positions[s].closeable_amount<=0:
            continue
        dfmcount = attribute_history(s,(g.run_count+1),'1m',['close'],skip_paused=True)
        if dfmcount.close[-1]
```

  * **功能说明** : 在盘中实时运行的函数，用于进行交易和风险管理。根据实时价格波动判断是否卖出股票，同时清理走势不佳的股票。

  * **关键逻辑** :

    * inntraday_trading 实现盘中止损和卖出逻辑。

    * clearn_every_bar 根据实时数据清理走势差的股票，控制下行风险。

6\. 收盘前的交易决策 (before_closing, sell_before_closing)

```python
def before_closing(context):
    sell_before_closing(context)
def sell_before_closing(context):
    df = history(1,'1d','close',context.portfolio.positions.keys())
    for s in list(context.portfolio.positions):
        if context.portfolio.positions[s].closeable_amount<=0:
            continue
        close_data = get_bars(s, count=2, unit='1m', fields=['open','high','low','close'],include_now=False)
        close_price = close_data['close'][-1]
        # 1.没涨停，卖
        if close_price/df[s][0]<1.098:
            R = order_target(s, 0)
        # 其他条件逻辑...
```

  * **功能说明** : 在收盘前根据股票涨停情况决定是否卖出持仓，确保在交易日结束前锁定收益或止损。

  * **关键逻辑** :

    * 根据是否涨停以及是否满足特定条件执行卖出操作，避免持仓风险过夜。

7\. 收盘后数据分析与选股 (after_market_close, consecutive_up_limit_stocks)

```python
def after_market_close(context):
    stock_list = all_limit_up_stocks(context.current_dt.strftime("%Y-%m-%d"))
    consecutive_up_limit_stocks(context,stock_list,context.current_dt)
    day_report(context)
    log.info('##############################################################')
def consecutive_up_limit_stocks(context,stock_list, thisDate):
    cur_data = get_current_data()
    stock_list = list(get_fundamentals(query(valuation.code).filter(valuation.circulating_market_cap<100,valuation.code.in_(stock_list)).order_by(indicator.roe.desc())).code)
    # 其他选股逻辑...
    g.buy_list = limit_stocks
```

  * **功能说明** : 在收盘后统计涨停股票，并通过财务指标进一步筛选出符合条件的股票作为次日的候选标的。

  * **关键逻辑** :

    * consecutive_up_limit_stocks 根据多天涨停情况筛选股票，并结合流通市值和 ROE 等指标优化股票池。

8\. 报告与清理 (day_report, clean_st_688)

```python
def day_report(context):
    current_returns=100*context.portfolio.returns
    log.info("当前收益：%.2f%%; 当前持仓数量: %s", current_returns, len(list(context.portfolio.positions.keys())))
    for s in context.portfolio.positions:
        cost=context.portfolio.positions[s].avg_cost
        price=context.portfolio.positions[s].price
        syl=(price/cost-1)*100
        log.info("    名称: %s,代码: %s,数量: %s,成本: %s,收益: %.2f%%",current_data[s].name,s,context.portfolio.positions[s].closeable_amount,context.subportfolios[0].long_positions[s].hold_cost,syl)
    log.info("总资产: {},当前收益：{}".format(context.portfolio.total_value,round(current_returns,2)))
def clean
_st_688(stocks):
    curr_data=get_current_data()
    stocks=[s for s in stocks if not (curr_data[s].is_st or('ST' in curr_data[s].name) or('*' in curr_data[s].name) or('退' in curr_data[s].name) or(s.startswith('688')))]
    return stocks
```

  * **功能说明** : 打印每日交易报告，记录持仓收益与总体收益，并清理不符合条件的股票如 ST 和科创板股票。

  * **关键逻辑** :

    * day_report 打印持仓详情，便于策略复盘。

    * clean_st_688 清除 ST、退市、科创板股票，保证策略标的质量。

### 策略总结

**短期涨停板追踪与风险控制策略** 利用集合竞价筛选、盘中实时交易、止损和止盈等多种技术手段，通过快速捕捉市场中的涨停板机会，追求高收益的同时严格控制下行风险。适合对短期市场有敏锐感知，并希望通过高频交易获取超额收益的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
