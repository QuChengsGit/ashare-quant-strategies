# 19、月度精选股票动态调整策略

# 策略简介

本策略旨在通过月度重新筛选并动态调整持仓，以获取表现最佳的股票。策略结合了基本面分析和技术面过滤，适用于市场中的优质个股，并避免了不符合标准的股票。优化后的策略考虑了滑点和避免未来数据，以提高实际操作的可靠性和稳定性。



### 策略代码与详细功能说明

### 1. initialize 函数

```python
def initialize(context):
    set_benchmark('000300.XSHG') # 设置基准指数
    log.set_level('order', 'error') # 设置日志等级为仅记录错误
    set_option('use_real_price', True) # 使用真实价格进行交易
    set_option('avoid_future_data', True) # 避免未来数据
    set_slippage(FixedSlippage(0.02)) # 设置固定滑点为0.02
    g.stock_num = 10 # 目标持股数量
    g.month = context.current_dt.month - 1 # 当前月份
```

  * **功能** ：初始化策略参数，包括基准指数、日志级别、滑点设置和持股数量。

### 2. before_trading_start 函数

```python
def before_trading_start(context):
    prepare_stock_list(context) # 准备股票池
    print(context.run_params.type) # 输出模拟交易参数
```

  * **功能** ：在开盘前运行，用于准备股票池并输出模拟交易参数。

### 3. handle_data 函数

```python
def handle_data(context, data):
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    # 每月首次执行选股
    if context.current_dt.month != g.month and hour == 9 and minute == 30:
        my_Trader(context)
        g.month = context.current_dt.month
    # 每天下午检查涨停股票
    if hour == 14 and minute == 0:
        check_limit_up(context)
    # 显示可用现金占总资产的百分比
    record(cash=context.portfolio.available_cash / context.portfolio.total_value * 100)
```

  * **功能** ：根据时间条件进行操作，包括每月重新筛选股票、每日检查涨停股票，以及记录现金占总资产的比例。

### 4. my_Trader 函数

```python
def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    stocks = filter_st_stock(stocks)
    stocks = filter_new_stock(context, stocks)
    stocks = choice_try_A(context, stocks)
    stocks = filter_paused_stock(stocks)
    stocks = filter_limit_stock(context, stocks)[:g.stock_num]
    cdata = get_current_data()
    slist(context, stocks)
    # 卖出不在新筛选列表中的股票
    for s in context.portfolio.positions:
        if s not in stocks and cdata[s].last_price < cdata[s].high_limit:
            log.info('Sell', s, cdata[s].name)
            order_target(s, 0)
    # 买入新选中的股票
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        psize = context.portfolio.available_cash / (g.stock_num - position_count)
        for s in stocks:
            if s not in context.portfolio.positions:
                log.info('Buy', s, cdata[s].name)
                order_value(s, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break
```

  * **功能** ：执行买卖操作。首先，卖出不在筛选列表中的股票。然后，买入新的符合条件的股票，确保持股数量不超过目标数量。

### 5. slist 函数

```python
def slist(context, stock_list):
    current_data = get_current_data()
    for stock in stock_list:
        df = get_fundamentals(query(valuation).filter(valuation.code == stock))
        print('股票代码：{0}, 名称：{1}, 总市值:{2:.2f}, 流通市值:{3:.2f}, PE:{4:.2f}, 股价：{5:.2f}'.format(
            stock, get_security_info(stock).display_name,
            df['market_cap'][0], df['circulating_market_cap'][0],
            df['pe_ratio'][0], current_data[stock].last_price))
```

  * **功能** ：打印筛选出的股票信息，包括名称、市值、PE 和股价。

### 6. prepare_stock_list 函数

```python
def prepare_stock_list(context):
    g.hold_list = []
    g.high_limit_list = []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    if g.hold_list:
        for stock in g.hold_list:
            df = get_price(stock, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1)
            if df['close'][0] >= df['high_limit'][0] * 0.98:
                g.high_limit_list.append(stock)
```

  * **功能** ：准备持有股票列表和昨日涨停股票列表，以便于后续操作。

### 7. check_limit_up 函数

```python
def check_limit_up(context):
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_current_data()
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info("[%s] 涨停打开，卖出" % (stock))
                order_target(stock, 0)
            else:
                log.info("[%s] 涨停，继续持有" % (stock))
```

  * **功能** ：检查昨日涨停的股票，如果今天开盘价低于涨停价，则卖出。

### 8. filter_kcbj_stock 函数

```python
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] in ['4', '8'] or stock[:2] == '68')]
```

  * **功能** ：过滤科创板和北交所的股票。

### 9. filter_paused_stock 函数

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
```

  * **功能** ：过滤停牌的股票。

### 10. filter_st_stock 函数

```python
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (current_data[stock].is_st or 'ST' in current_data[stock].name or '*' in current_data[stock].name or '退' in current_data[stock].name)]
```

  * **功能** ：过滤ST及其他具有退市标签的股票。

### 11. filter_limit_stock 函数

```python
def filter_limit_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or (current_data[stock].low_limit < last_prices[stock][-1] < current_data[stock].high_limit)]
```

  * **功能** ：过滤涨停的股票，但保留已持有的股票。

### 12. get_dividend_ratio_filter_list 函数

```python
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365*3)
    interval = 1000
    list_len = len(stock_list)
    q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
    ).filter(
        finance.STK_XR_XD.a_registration_date >= time0,
        finance.STK_XR_XD.a_registration_date <= time1,
        finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)]))
    df = finance.run_query(q)
    if list_len > interval:
        df_num = list_len // interval
        for i in range(df_num):
            q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
            ).filter(
                finance.STK_XR_XD.a_registration_date >= time0,
                finance.STK_XR_XD.a_registration_date <= time1,
                finance.STK_XR_XD.code.in_(stock_list[interval*(i+1):min(list_len, interval*(i+2))]))
            temp_df = finance.run_query(q)
            df = df.append(temp_df)
    dividend = df.fillna(0)
    dividend = dividend
.groupby('code').sum().reset_index()
    dividend = dividend.sort_values(sort, ascending=False)
    return dividend[(dividend[sort] >= p1) & (dividend[sort] <= p2)]['code'].tolist()
```

  * **功能** ：筛选出符合股息率条件的股票。



### 结论与实施

  * **目标** ：优化月度股票选取和动态调整策略，以提高股票池质量和策略稳定性。

  * **关键步骤** ：

    1. 每月重新筛选股票池，确保投资组合的质量。

    2. 每天检查涨停股票，确保及时卖出。

    3. 使用技术面和基本面过滤工具，确保选股质量。

  * **注意事项** ：务必避免使用未来数据，确保策略的实际效果与模拟效果一致。关注滑点对策略的影响，并定期调整策略参数以适应市场变化。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
