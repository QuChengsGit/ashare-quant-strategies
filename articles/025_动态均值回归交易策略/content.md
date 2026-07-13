# 25、动态均值回归交易策略

### 策略简介

“动态均值回归交易策略”是基于均值回归的概念，通过对股票的短期均值表现进行筛选，结合多时段的价格动态进行买卖决策。策略使用了限制买卖时间段和尾盘撮合的方式，确保交易在合适的时间点进行，从而捕捉市场中的价格波动机会，达到获取收益的目的。

### 策略结构与功能

### 1. 初始化函数

```python
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    # 全局变量初始化
    g.sel_stock = None
    g.strategy_starttime = time(10, 20)  # 策略开始买卖时间
    g.strategy_endtime = time(14, 55)    # 策略尾盘撮合买入时间
    # 交易费用设置：买入时万分之二点五，卖出时万分之二点五加千分之一印花税
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.00025, close_commission=0.00025, min_commission=5), type='stock')
    # 定时任务设置
    run_weekly(weekly, weekday=1, time='09:31', reference_security='000300.XSHG')
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
```

  * **功能说明** :

    * 初始化策略的基本设置，包括基准指数、交易费用、日志过滤和全局变量的初始化。

    * 设置策略执行的时间节点。

### 2. 持仓调整函数

**2.1 周度调仓函数**

```python
def weekly(context):
    g.sel_stock = None
    current_data = get_current_data()
    stock_list = get_all_securities().index.tolist()
    # 获取最近5天的收盘价并计算均值
    last_5_prices = history(count=5, field='close', security_list=stock_list)
    last_5_prices = pd.DataFrame({'mean_val': last_5_prices.mean()})
    # 均值升序排序
    last_5_prices_sort = last_5_prices.sort_values(by='mean_val', ascending=True)
    # 选择均值大于等于1.5的股票
    last_5_prices_stock = last_5_prices_sort.query('mean_val >= 1.5').index.tolist()
    # 去除停牌、ST股以及带有退市风险的股票
    for security in last_5_prices_stock:
        if not current_data[security].paused and not current_data[security].is_st and '*' not in current_data[security].name and '退' not in current_data[security].name:
            g.sel_stock = security
            break
    if g.sel_stock is not None:
        log.info(f"选定股票: {g.sel_stock} - {get_security_info(g.sel_stock).display_name}")
        # 卖出不在持仓列表的股票
        sell_list = set(context.portfolio.positions.keys()) - set([g.sel_stock])
        for stock in sell_list:
            order_target_value(stock, 0)
    else:
        for stock in context.portfolio.positions.keys():
            order_target_value(stock, 0)
```

  * **功能说明** :

    * 每周一进行持仓调整，选择出5日均值较低但大于1.5的股票，作为下一周的目标持仓。

    * 调整持仓，卖出不符合条件的股票。

### 3. 交易函数

**3.1 开盘前准备**

```python
def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + context.current_dt.strftime("%Y-%m-%d %H:%M:%S"))
    g.not_buy_flg = 1
    g.not_sell_flg = 1
    g.last_buy_orderid = None
    g.last_sell_orderid = None
    g.last_buy_price = 0
    g.last_sell_price = 0
    g.price_50m = {'open': 0.000, 'close': 0.000, 'high': 0.000, 'low': 0.000}
    g.price_before_close = 0.000
```

  * **功能说明** :

    * 每天开盘前重置交易标志位和全局变量，为当天交易做好准备。

**3.2 开盘期间交易逻辑**

```python
def market_open(context):
    current_data = get_current_data()
    if g.sel_stock is None:
        return
    if context.current_dt.time() >= g.strategy_starttime:
        if g.not_buy_flg == 1:
            now_buy_price = get_buy_price(context)
            cancel_previous_order(g.last_buy_orderid)
            g.last_buy_price = now_buy_price
            buy_count = int(context.portfolio.available_cash / now_buy_price / 100) * 100
            if buy_count >= 100:
                new_order = order(g.sel_stock, buy_count, LimitOrderStyle(now_buy_price))
                update_order_status(new_order, is_buy=True)
        if context.current_dt.time() < g.strategy_endtime and g.not_sell_flg == 1:
            now_sell_price = get_sell_price(context)
            cancel_previous_order(g.last_sell_orderid)
            if g.sel_stock in context.portfolio.positions and context.portfolio.positions[g.sel_stock].closeable_amount > 0:
                g.last_sell_price = now_sell_price
                new_order = order(g.sel_stock, -context.portfolio.positions[g.sel_stock].closeable_amount, LimitOrderStyle(now_sell_price))
                update_order_status(new_order, is_buy=False)
```

  * **功能说明** :

    * 交易逻辑根据时间段动态获取买入和卖出价格，并在不同的时间段内进行买入和卖出操作。

**3.3 获取买卖价格函数**

```python
def get_buy_price(context):
    sel_stock_price = attribute_history(g.sel_stock, 1, unit='50m', fields=('open','close','high','low'), skip_paused=True, df=True, fq='pre')
    if context.current_dt.time() >= g.strategy_starttime and context.current_dt.time() < g.strategy_endtime:
        return sel_stock_price['low'][0]
    else:
        return sel_stock_price['close'][0]
def get_sell_price(context):
    sel_stock_price = attribute_history(g.sel_stock, 1, unit='50m', fields=('open','close','high','low'), skip_paused=True, df=True, fq='pre')
    if context.current_dt.time() >= g.strategy_starttime and context.current_dt.time() < g.strategy_endtime:
        return sel_stock_price['high'][0]
    else:
        return sel_stock_price['close'][0]
```

  * **功能说明** :

    * 获取当前时间段的最低价作为买入价，最高价作为卖出价。

4\. 收盘后处理

```python
def after_market_close(context):
    log.info(f"函数运行时间(after_market_close): {str(context.current_dt.time())}")
    trades = get_trades()
    for _trade in trades.values():
        log.info(f"成交记录：{str(_trade)}")
    log.info('一天结束')
    log.info('##############################################################')
```

  * **功能说明** :

    * 收盘后记录当天所有的交易信息，并输出到日志中，方便后续分析。

### 5. 辅助函数

**5.1 取消前一订单**

```python
def cancel_previous_order(order_id):
    if order_id is not None:
        orders = get_open_orders()
        for _order in orders.values():
            if _order.order_id == order_id:
                cancel_order(_order)
```

  * **功能说明** :

    * 用于取消之前未成交的订单，避免多次下单冲突。

**5.2 更新订单状态**

```python
def update_order_status(order, is_buy):
    if order is not None:
        if str(order.status) == 'held':
            g.not_sell_flg = 0 if is_buy else 1
        else:
            if is_buy:
                g.last_buy_orderid = order.order_id
            else:
                g.last_sell_orderid = order.order_id
```

  * **功能说明** :

    * 更新买卖订单状态，用于控制订单流和避免重复下单。



### 策略总结

“动态均值回归交易策略”通过分析股票短期均值和市场价格动态，选择在适当的时间点进行买卖操作。策略对时段的选择

和订单管理有着严格的控制，旨在捕捉市场中的短期波动，降低交易风险，并提高收益潜力。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
