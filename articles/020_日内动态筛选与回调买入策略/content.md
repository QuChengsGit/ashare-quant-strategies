# 20、日内动态筛选与回调买入策略

以下是对策略各部分功能代码的详细技术文档说明：



**1\. 初始化函数 initialize**

**功能** ：设置策略的初始参数和运行规则。

```python
def initialize(context):
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    set_slippage(FixedSlippage(0.02))  # 设置滑点
    set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))  # 设置交易佣金
    set_benchmark('399303.XSHE')  # 设置基准指数
    g.choice = 500  # 股票池大小
    g.amount = 7  # 最大持仓股票数量
    g.muster = []  # 筛选后的股票列表
    g.bucket = []  # 备选股票列表
    g.summit = {}  # 存储其他信息
    log.set_level('order', 'warning')  # 设置日志级别
    run_daily(buy, time='9:30', reference_security='399303.XSHE')  # 每日9:30执行买入
    run_daily(sell, time='10:30', reference_security='399303.XSHE')  # 每日10:30执行卖出
```



**2\. 股票过滤函数**

**2.1 过滤停牌股票**

**功能** ：排除停牌股票。

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
```

**2.2 过滤ST及其他退市标签股票**

**功能** ：排除ST及其他退市标签股票。

```python
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list
            if not current_data[stock].is_st
            and 'ST' not in current_data[stock].name
            and '*' not in current_data[stock].name
            and '退' not in current_data[stock].name]
```

**2.3 过滤科创北交股票**

**功能** ：排除科创板及北交所股票。

```python
def filter_kcbj_stock(stock_list):
    for stock in stock_list[:]:
        if stock[0] == '4' or stock[0] == '8' or stock[:2] == '68' or stock[:2] == '30':
            stock_list.remove(stock)
    return stock_list
```

**2.4 过滤涨停的股票**

**功能** ：排除涨停股票。

```python
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[stock][-1] < current_data[stock].high_limit]
```

**2.5 过滤跌停的股票**

**功能** ：排除跌停股票。

```python
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[stock][-1] > current_data[stock].low_limit]
```

**2.6 过滤次新股**

**功能** ：排除上市不久的次新股。

```python
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [stock for stock in stock_list if not yesterday - get_security_info(stock).start_date < datetime.timedelta(days=375)]
```



**3\. 每日盘前处理函数 before_trading_start**

**功能** ：在每个交易日开盘前筛选股票池。

```python
def before_trading_start(context):
    log.info('------------------------------------------------------------')
    fundamentals_data = get_fundamentals(query(valuation.code, valuation.market_cap).order_by(valuation.market_cap.asc()).limit(g.choice))
    stocks = list(fundamentals_data['code'])
    current_data = get_current_data()
    g.muster = [s for s in stocks if not current_data[s].paused and not current_data[s].is_st and 'ST' not in current_data[s].name and '*' not in current_data[s].name and '退' not in current_data[s].name and current_data[s].low_limit < current_data[s].day_open < current_data[s].high_limit]
    g.muster = filter_paused_stock(g.muster)
    g.muster = filter_st_stock(g.muster)
    g.muster = filter_kcbj_stock(g.muster)
    g.muster = filter_limitup_stock(context, g.muster)
    g.muster = filter_limitdown_stock(context, g.muster)
```



**4\. 买入函数 buy**

**功能** ：根据筛选条件和策略买入股票。

```python
def buy(context):
    data_today = get_current_data()
    available_slots = g.amount - len(context.portfolio.positions)
    if available_slots <= 0:
        print("no position")
        return
    allocation = context.portfolio.cash / available_slots
    for s in g.muster:
        if len(context.portfolio.positions) == g.amount:
            break
        if (history(5, '1d', 'paused', s).max().values[0] == 0):
            low = history(4, '1d', 'low', s).min().values[0]
            high = history(4, '1d', 'high', s).max().values[0]
            percent = (high - low) / low * 100
            if percent <= 10:
                open_price_today = data_today[s].day_open
                prev_close = get_price(s, count=1, end_date=context.previous_date).iloc[-1]['close']
                his = history(60, '1d', 'close', s)
                ema = talib.EMA(his.values.flatten(), timeperiod=5)[-1]
                if prev_close > ema:
                    if get_price(s, count=1, end_date=context.previous_date).iloc[-1]['low'] > open_price_today:
                        order(s, int(allocation / open_price_today))
```



**5\. 卖出函数 sell**

**功能** ：卖出持仓股票。

```python
def sell(context):
    data_today = get_current_data()
    for s in context.portfolio.positions:
        print("sell:" + s)
        order_target(s, 0)
```



### 总结

**策略名称** ：“日内动态筛选与回调买入策略”

**目标** ：通过动态筛选股票池和回调买入策略来优化股票的选择和持仓管理，提高策略的收益和稳定性。

**步骤** ：

  1. **初始化** ：设置策略参数、滑点、佣金等，并定义买入和卖出时间。

  2. **股票筛选** ：实现多个过滤函数，排除停牌、ST股、涨跌停股、科创板及北交所股票、次新股等。

  3. **每日处理** ：在开盘前筛选符合条件的股票。

  4. **买入** ：根据策略条件决定是否买入，并根据可用资金进行分配。

  5. **卖出** ：卖出所有持仓股票。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
