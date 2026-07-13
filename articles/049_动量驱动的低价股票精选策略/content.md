# 49、动量驱动的低价股票精选策略

# 1. 策略概述

**动量驱动的低价股票精选策略** 是一种基于动量指标的选股策略，通过筛选价格较低、动量较强的股票进行投资，以期在市场中获得超额收益。策略的核心思想是利用股票的动量效应，选择那些价格在过去一段时间内上涨幅度较大的股票，同时避开次新股、停牌股和ST股等不确定性较大的股票。

# 2. 策略各部分功能代码详细技术文档说明

## 2.1 策略初始化 (initialize)

策略初始化时，设定基准指数、交易滑点、交易成本等基本参数，并设置每日运行的函数。策略会在开盘前筛选股票，并在开盘时执行交易。

```python
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 避免使用未来数据
    set_option("avoid_future_data", True)
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    # 过滤order中低于error级别的日志
    log.set_level('order', 'error')
    # 策略参数
    g.stock_num = 10  # 持仓数量
    g.day_count = 91  # 动量计算天数
    g.stock_price = 5  # 股价筛选条件
    # 每日开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    # 每日开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    # 每日收盘后打印交易信息
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')
```

## 2.2 开盘前股票筛选 (before_market_open)

在开盘前筛选股票。首先过滤掉不符合条件的股票（如次新股、停牌股、ST股等），然后根据动量指标选出动量最强的股票。

```python
def before_market_open(context):
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    # 获取所有可交易的股票列表
    initial_list = get_all_securities().index.tolist()
    # 过滤股票
    initial_list = filter_trade_stock(context, initial_list)
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_paused_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 根据动量筛选股票
    next_holding_codes = get_momentum(context, initial_list)
    # 获取当前持仓的股票代码
    holding_codes = list(context.portfolio.positions.keys())
    # 昨日持仓但今日不再持有的股票
    g.security1 = [x for x in holding_codes if x not in next_holding_codes]
    # 今日新增持仓的股票
    g.security2 = [y for y in next_holding_codes if y not in holding_codes]
```

## 2.3 开盘时执行交易 (market_open)

根据筛选结果调整持仓。卖出不再持有的股票，买入新选中的股票。

```python
def market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    # 卖出不再持有的股票
    for stock in g.security1:
        order_target(stock, 0)
    # 买入新选中的股票
    cash = context.portfolio.available_cash / len(g.security2)
    for stock in g.security2:
        order_value(stock, cash)
```

## 2.4 动量计算函数 (get_momentum)

计算每只股票的动量（即一定时间段内的收益率），并选出动量最大的股票。

```python
def get_momentum(context, stock_list):
    stock_momentum = {}
    for stock in stock_list:
        # 计算股票的动量
        df = get_price(stock, count=g.day_count, end_date=context.current_dt - datetime.timedelta(days=1), fields=['close'], skip_paused=True, panel=False)
        if df['close'][-1] < g.stock_price:
            continue
        stock_momentum[stock] = (df['close'][-1] - df['close'][0]) / df['close'][0]
    # 返回动量最大的股票
    next_hold = min_dict(stock_momentum, g.stock_num)
    return next_hold
```

## 2.5 过滤函数

策略通过多种过滤函数筛选掉不符合条件的股票。

```python
# 过滤主板、中小板股票
def filter_trade_stock(context, stock_list):
    return [stock for stock in stock_list if stock[:2] == '60' or stock[:2] == '00']
# 过滤次新股
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [stock for stock in stock_list if not yesterday - get_security_info(stock).start_date < datetime.timedelta(days=250)]
# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
# 过滤ST股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
```

## 2.6 交易信息打印 (print_trade_info)

每日收盘后打印当天的交易记录和持仓情况，帮助用户监控策略的执行情况。

```python
def print_trade_info(context):
    # 打印当天成交记录
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：'+str(_trade))
    # 打印账户信息
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print('代码:{}'.format(securities))
        print('成本价:{}'.format(format(cost, '.2f')))
        print('现价:{}'.format(price))
        print('收益率:{}%'.format(format(ret, '.2f')))
        print('持仓(股):{}'.format(amount))
        print('市值:{}'.format(format(value, '.2f')))
```

# 3. 优化建议

  1. **多因子筛选** ：在动量因子之外，可以结合其他因子（如估值、质量等）进一步优化股票选择，提高策略的稳定性和盈利能力。

  2. **动态仓位管理** ：根据市场环境动态调整持仓比例，以更好地适应市场波动，控制回撤。

  3. **止盈止损机制** ：引入止盈和止损机制，以及时锁定收益或减少亏损。

4\. 总结

**动量驱动的低价股票精选策略** 通过严格的筛选条件和动量计算，力求在市场中捕捉到具有上涨潜力的股票。该策略每日进行股票筛选和持仓调整，适合在波动性较大的市场环境中寻找稳定的投资机会。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
