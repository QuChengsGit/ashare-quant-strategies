# 34、多维量能与竞价策略

# 1. 策略概述

本策略通过多维度量能分析、竞价开盘过滤以及动态调仓机制，结合基本面和技术指标筛选优质股票，进行买卖操作。策略核心包括对市场的短期量能变化进行监控和分析，判断市场强弱信号，并通过竞价开盘价与前一日收盘价的比较来进行股票的选择和交易。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (after_code_changed)

该模块在策略初始化或代码变动后运行，用于设置策略的全局参数、回测条件和运行的时间节点。

```python
def after_code_changed(context):
    log.info('初始函数开始运行且全局只运行一次')
    unschedule_all()
    set_params()    # 设置策略参数
    set_variables() # 设置中间变量
    set_backtest()  # 设置回测条件
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 设定每天的运行时间
    run_daily(before_market_open, time='7:00')
    run_daily(call_auction, time='09:26')
    run_daily(market_run, time='14:55')
```

## 2.2 策略参数设置模块 (set_params)

用于设置策略的全局参数，包括指数基准、竞价开盘上下限、止盈门槛、量能过滤参数等。

```python
def set_params():
    g.index = 'all'  # 指数基准：all-所有股票
    g.auction_open_highlimit = 0.985  # 竞价开盘上限
    g.auction_open_lowlimit = 0.945   # 竞价开盘下限
    g.profit_line = 1.05  # 止盈门槛
    g.volume_control = 2   # 量能控制模式
    g.volume_period = 20   # 放量控制周期
    g.volume_ratio = 5     # 放量控制比例
    g.sell_mode = 0        # 持仓量能过滤模式
    g.sell_vol_period = 120  # 持仓放量控制周期
    g.sell_vol_ratio = 0.9  # 持仓放量控制比例
```

## 2.3 中间变量设置模块 (set_variables)

设置策略运行所需的中间变量，如持仓数量、股票池大小等。

```python
def set_variables():
    g.stocknum = 0  # 持仓数量（0代表全取）
    g.poolnum = 1 * g.stocknum  # 参考池数
```

## 2.4 回测条件设置模块 (set_backtest)

设置回测条件，包括基准指数、真实价格、滑点等。

```python
def set_backtest():
    if g.index == 'all':
        set_benchmark('000001.XSHG')
    else:
        set_benchmark(g.index)
    set_option('use_real_price', True)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    log.set_level('order', 'error')  # 设置日志等级
```

## 2.5 开盘前运行模块 (before_market_open)

在每日开盘前执行，构建股票池，并进行多维度过滤。

```python
def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    today_date = context.current_dt.date()
    lastd_date = context.previous_date
    befor_date = get_trade_days(end_date=today_date, count=3)[0]
    all_data = get_current_data()
    g.poolist = []
    g.sell_list = []
    # 基准指数票池筛选
    if g.index == 'all':
        stocklist = list(get_all_securities(['stock']).index)
    elif g.index == 'zz':
        stocklist = get_index_stocks('000300.XSHG', date=None) + get_index_stocks('000905.XSHG', date=None) + get_index_stocks('000852.XSHG', date=None)
    else:
        stocklist = get_index_stocks(g.index, date=None)
    stocklist = [stockcode for stockcode in stocklist if not all_data[stockcode].paused]
    stocklist = [stockcode for stockcode in stocklist if not all_data[stockcode].is_st]
    stocklist = [stockcode for stockcode in stocklist if '退' not in all_data[stockcode].name]
    stocklist = [stockcode for stockcode in stocklist if stockcode[0:3] != '688']
    stocklist = [stockcode for stockcode in stocklist if (today_date - get_security_info(stockcode).start_date).days > 365]
    poollist = get_up_filter_jiang(context, stocklist, lastd_date, 1, 1, 0)
    list_201 = get_up_filter_jiang(context, poollist, lastd_date, 20, 1, 0)
    g.poollist = optimize_filter(context, list_201, 'L')
    # 增加天量/爆量过滤
    if g.volume_control != 0:
        g.poollist = get_highvolume_filter(context, g.poollist, g.volume_control, g.volume_period, g.volume_ratio)
    # 增加持仓股的量能卖出控制
    if g.sell_mode != 0 and len(context.portfolio.positions) != 0:
        stocklist = list(context.portfolio.positions)
        g.sell_list = get_highvolume_filter(context, stocklist, g.sell_mode, g.sell_vol_period, g.sell_vol_ratio)
```

## 2.6 竞价运行模块 (call_auction)

在每日竞价期间执行，根据竞价开盘价与前一日收盘价的比例筛选股票并执行交易。

```python
def call_auction(context):
    log.info('函数运行时间(Call_auction)：' + str(context.current_dt.time()))
    current_data = get_current_data()
    today_date = context.current_dt.date()
    lastd_date = context.previous_date
    buy_list = []
    df_auction = get_call_auction(g.poollist, start_date=today_date, end_date=today_date, fields=['time', 'current', 'volume', 'money'])
    if len(g.sell_list) == 0:
        log.info('今日早盘无卖信')
    else:
        for stockcode in context.portfolio.positions:
            if not current_data[stockcode].paused and stockcode in g.sell_list:
                sell_stock(context, stockcode, 0)
    for i in range(len(df_auction)):
        stockcode = df_auction.code.values[i]
        price = df_auction.current.values[i]
        df_price = get_price(stockcode, end_date=lastd_date, frequency='daily', fields=['close'], count=5)
        if g.auction_open_lowlimit < price / df_price.close[-1] < g.auction_open_highlimit:
            buy_list.append(stockcode)
    if len(buy_list) == 0:
        log.info('今日无买信')
        return
    log.info('今日买信共%d只:' % len(buy_list))
    total_value = context.portfolio.total_value
    buy_cash = 0.5 * total_value / len(buy_list)
    for stockcode in buy_list:
        if stockcode not in context.portfolio.positions:
            buy_stock(context, stockcode, buy_cash)
```

## 2.7 尾盘运行模块 (market_run)

在每日尾盘阶段执行，对当前持仓进行检查，决定是否卖出非涨停股票。

```python
def market_run(context):
    log.info('函数运行时间(market_close):' + str(context.current_dt.time()))
    current_data = get_current_data()
    for stockcode in context.portfolio.positions:
        if not current_data[stockcode].paused and current_data[stockcode].last_price != current_data[stockcode].high_limit:
            log.info('非涨停即出%s' % stockcode)
            sell_stock(context, stockcode, 0)
```

## 2.8 辅助函数

这些函数包括买入、卖出操作以及各种筛选和过滤的辅助函数。

```python
def buy_stock(context, stockcode, cash):
    today_date = context.current_dt.date()
    current_data = get_current_data()
    last_price = current_data[stockcode].last_price
    if stockcode[0:3] == '688':
        if order_target_value(stockcode, cash, MarketOrderStyle(1.1 * last_price)) is not None:
            log.info('%s买入%s' % (today_date, stockcode))
    else:
        if order_target_value(stockcode, cash) is not None:
            log.info('%s买入%s' % (today_date, stockcode))
def sell_stock(context, stockcode, cash):
    today_date = context.current_dt.date()
    current_data = get_current_data()
    last_price = current_data[stockcode].last_price
    if stockcode[0:3
] == '688':
        if order_target_value(stockcode, cash, MarketOrderStyle(0.9 * last_price)) is not None:
            log.info('%s卖出%s' % (today_date, stockcode))
    else:
        if order_target_value(stockcode, cash) is not None:
            log.info('%s卖出%s' % (today_date, stockcode))
```

# 3. 策略优化建议

  1. **动态调整量能参数** ：针对不同的市场环境，可以动态调整量能的过滤参数，提高策略的灵活性。

  2. **增加风险控制机制** ：如设置更详细的止损条件或动态调整仓位比例，以降低市场波动带来的风险。

  3. **引入更多技术指标** ：结合其他技术指标，如MACD、RSI等，进一步提升股票筛选的精度。

通过以上策略，投资者能够在竞价阶段和日内交易时，结合量能和价格的动态变化，捕捉市场的短期机会，从而实现更高的收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
