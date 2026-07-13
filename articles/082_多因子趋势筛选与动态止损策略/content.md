# 82、多因子趋势筛选与动态止损策略

# 策略概述

**多因子趋势筛选与动态止损策略** 是一种结合了多因子趋势筛选和动态止损的量化投资策略。通过对股票的历史价格进行趋势分析，筛选出符合预期趋势的股票，然后利用多个止损机制（如动态回撤、均线、RSI等）对持仓股票进行风险控制。策略根据设定的周期进行定期调仓，以确保投资组合的收益和风险平衡。

### 各部分功能代码与详细说明

1\. 初始化与策略设置 (after_code_changed)

```python
def after_code_changed(context):
    log.info('初始函数开始运行且全局只运行一次')
    unschedule_all()  # 取消之前所有的调度
    set_params()      # 设置策略参数
    set_variables()   # 设置中间变量
    set_backtest()    # 设置回测条件
    # 股票交易手续费设置
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 运行调度设置
    run_daily(before_market_open, time='7:00')  # 开盘前运行
    run_daily(market_open, time='09:30')        # 开盘时运行
```

  * **功能说明** : 初始化策略时设置各项参数和变量，并安排每日开盘前和开盘时的运行函数。

  * **关键逻辑** :

    * 取消之前的调度，确保新的调度生效。

    * 设置全局参数（策略参数、变量、回测条件等）。

2\. 设置策略参数 (set_params)

```python
def set_params():
    g.index = '000905.XSHG'  # 股票池基准指数
    g.pool_filter = 'R'  # 涨幅过滤选项
    g.strategy = 'T'  # 策略选择：T代表趋势策略
    g.fields_name = 'close'  # 选股时使用的价格字段
    g.short_duration = 20  # 短期趋势周期
    g.trend_up = 999  # 趋势斜率上限
    g.trend_down = 0  # 趋势斜率下限
    g.lostcontrol = 2  # 动态止损类型
    g.drop_line = 0.75  # 动态止损回撤线
    g.drop_ma_days = 20  # 动态止损均线周期
```

  * **功能说明** : 设置策略的主要参数，包括股票池的基准指数、选股策略、趋势斜率范围、动态止损机制等。

  * **关键逻辑** :

    * 根据设定的策略参数，筛选符合条件的股票，并进行风险控制。

3\. 设置中间变量 (set_variables)

```python
def set_variables():
    g.stocknum = 5  # 持仓股票数量
    g.poolnum = 0.3  # 股票池的比例
    g.shiftdays = 1  # 换仓周期
    g.day_count = 0  # 换仓计数器
```

  * **功能说明** : 设置一些用于控制策略运行的中间变量，如持仓股票数量、换仓周期等。

  * **关键逻辑** :

    * 定义了持仓股票数量和换仓周期的相关参数，以便在策略中动态调整持仓。

4\. 设置回测条件 (set_backtest)

```python
def set_backtest():
    set_benchmark(g.index)  # 设定基准指数
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    log.set_level('order', 'error')  # 设置报错等级
```

  * **功能说明** : 设置回测条件，确保策略在历史回测时符合预期。

  * **关键逻辑** :

    * 设定基准指数，并开启真实价格模式，避免未来数据的使用。

5\. 开盘前函数 (before_market_open)

```python
def before_market_open(context):
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    today_date = context.current_dt.date()
    lastd_date = context.previous_date
    all_data = get_current_data()
    # 止损控制
    if g.lostcontrol != 0:
        holdlist = list(context.portfolio.positions)
        g.selllist = lost_control(context, holdlist, today_date)
        log.info('%s损控-%s卖出:' % (today_date, g.lostcontrol))
        log.info(g.selllist)
    # 判断是否是换仓日
    if (g.day_count % g.shiftdays == 0):
        log.info('今天是换仓日，开仓')
        g.adjustpositions = True
    else:
        log.info('今天是旁观日，持仓')
        g.adjustpositions = False
        return
    # 生成股票池
    stocklist = generate_stock_pool(context, today_date, lastd_date)
    g.buylist = select_stocks(context, stocklist)
    log.info('今日买信:')
    log.info(g.buylist)
```

  * **功能说明** : 开盘前的主要准备工作，包括止损判断、换仓日判断以及生成股票池和选股列表。

  * **关键逻辑** :

    * 判断是否需要调仓，并生成买入和卖出股票列表。

6\. 生成股票池函数 (generate_stock_pool)

```python
def generate_stock_pool(context, today_date, lastd_date):
    # 构建基准指数股票池
    stocklist = get_index_stocks(g.index, date=None)
    stocklist = [stockcode for stockcode in stocklist if not get_current_data()[stockcode].paused]
    stocklist = [stockcode for stockcode in stocklist if not get_current_data()[stockcode].is_st]
    stocklist = [stockcode for stockcode in stocklist if '退' not in get_current_data()[stockcode].name]
    stocklist = [stockcode for stockcode in stocklist if (today_date - get_security_info(stockcode).start_date).days > 365]
    return stocklist
```

  * **功能说明** : 根据预设的基准指数，生成初步的股票池。

  * **关键逻辑** :

    * 剔除停牌、ST及退市风险股票，并筛选上市满一年的股票。

7\. 选股函数 (select_stocks)

```python
def select_stocks(context, stocklist):
    # 根据趋势过滤股票
    stocklist = get_trend_filter(context, stocklist, context.previous_date, g.short_duration, '1d', g.trend_up, g.trend_down)
    # 涨幅过滤
    if 'R' in g.pool_filter:
        stocklist = get_rise_filter(context, stocklist, g.index, g.short_duration, g.rise_uplimit)
    # 按照持仓数量选取股票
    if g.stocknum == 0 or len(stocklist) <= g.stocknum:
        return stocklist
    else:
        return stocklist[:g.stocknum]
```

  * **功能说明** : 根据趋势过滤和涨幅过滤从股票池中筛选出最终的持仓股票。

  * **关键逻辑** :

    * 使用趋势和涨幅筛选出符合策略的股票，最终根据持仓数量限制选出股票。

8\. 止损控制函数 (lost_control)

```python
def lost_control(context, stocklist, check_date):
    poollist = []
    for stockcode in context.portfolio.positions:
        cost = context.portfolio.positions[stockcode].avg_cost
        price = context.portfolio.positions[stockcode].price
        ret = price / cost
        # 动态止损判断
        if g.lostcontrol == 2:
            df_price = get_price(stockcode, count=g.drop_ma_days, end_date=context.previous_date, frequency='daily', fields=['high', 'close'])
            high_max = df_price['high'].max()
            last_price = df_price['close'].values[-1]
            if last_price / high_max < g.drop_line:
                poollist.append(stockcode)
    return poollist
```

  * **功能说明** : 根据设置的动态止损规则，判断是否需要卖出持仓股票。

  * **关键逻辑** :

    * 动态止损通过回撤线和均线判断是否达到卖出条件，如果满足条件则加入卖出列表。

### 总结

**多因子趋势筛选与动态止损策略** 通过多因子趋势分析和严格的止损机制，在保证收益的同时有效控制风险。该策略适合那些追求稳健收益，并希望通过趋势分析和动态止损来降低投资风险的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
