# 63、动态涨停板追踪与风控策略

### 策略介绍

**动态涨停板追踪与风控策略** 是一种针对涨停板交易的策略，旨在通过识别并买入可能涨停的股票，同时根据设定的卖出规则和止盈止损条件，及时退出市场，确保收益的同时控制风险。该策略特别适用于短线交易者，利用开盘后的市场波动机会，实现快速收益。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
from datetime import timedelta
from jqdata import *
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("match_by_signal", True)  # 强制撮合
    log.set_level('order', 'error')  # 过滤掉order系列API产生的比error级别低的log
    g.help_stock = {}  # 存储可能涨停的股票及其涨停价，格式：{股票代码：今日涨停价}
    g.max_stock_num = 20  # 最大持仓20只股票
    # 调度函数
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_run, time='every_bar', reference_security='000300.XSHG')
```

技术说明：

  * **初始化** ：策略的初始化函数定义了基准指数、交易选项和日志级别，设定了最大持仓数量，并定义了存储可能涨停股票的全局变量。

2\. 市场运行与交易执行

```python
def market_run(context):
    time_now = context.current_dt.strftime('%H:%M:%S')
    if time_now <= '09:31:00':
        return
    cash = context.portfolio.available_cash
    if cash > 5000 and len(context.portfolio.positions) < g.max_stock_num:
        bars = get_bars(list(g.help_stock.keys()), count=2, unit='1m', fields=['close'], include_now=True, end_dt=context.current_dt)
        for stock in g.help_stock:
            if stock in context.portfolio.positions:
                continue
            close2m = bars[stock]['close']
            if close2m[-2] < close2m[-1] == g.help_stock[stock]:
                function_buy(context, stock)
    # 卖出条件判断与执行
    holdings = [s for s in context.portfolio.positions if context.portfolio.positions[s].closeable_amount > 0]
    if not holdings:
        return
    # 获取昨日和今日的数据
    df_pre = get_price(holdings, count=1, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], panel=False).set_index('code')
    today_start = context.current_dt.replace(hour=9, minute=31, second=0)
    df_all_day = get_price(holdings, start_date=today_start, end_date=context.current_dt,
                           frequency='1m', fields=['high', 'close', 'high_limit'], panel=False)
    s_high_today = df_all_day.groupby('code')['high'].max()
    s_count_limit_all_day = df_all_day.groupby('code').apply(lambda x: (x.close == x.high_limit).sum())
    s_count_limit_first_10m = df_all_day.groupby('code').apply(lambda x: (x.close == x.high_limit)[:10].sum())
    curr_data = get_current_data()
    for stock in holdings:
        current_price = curr_data[stock].last_price
        day_open_price = curr_data[stock].day_open
        day_high_limit = curr_data[stock].high_limit
        day_low_limit = curr_data[stock].low_limit
        if current_price <= day_low_limit:
            continue
        pre_close = df_pre['close'][stock]
        pre_high_limit = df_pre['high_limit'][stock]
        high_all_day = s_high_today[stock]
        count_limit_all_day = s_count_limit_all_day[stock]
        count_limit_before10 = s_count_limit_first_10m[stock]
        cost = context.portfolio.positions[stock].avg_cost
        # 一系列卖出条件
        if current_price >= cost * 2:
            order_target(stock, 0)
        elif current_price < cost * 0.92 and current_price < day_open_price and pre_close == pre_high_limit:
            order_target(stock, 0)
        # ...（其他卖出条件）
        elif day_open_price > pre_close * 1.045 and current_price < day_open_price and time_now <= '09:33:00':
            order_target(stock, 0)
```

技术说明：

  * **市场运行逻辑** ：每分钟检查持仓情况并根据特定条件决定是否买入或卖出股票，确保在涨停行情中捕获机会并在适当时机退出。

3\. 买入执行函数

```python
def function_buy(context, stock):
    open_cash = 0
    stock_owner = context.portfolio.positions
    if len(stock_owner) < 20:
        open_cash = context.portfolio.available_cash / (20 - len(stock_owner))
    if stock not in stock_owner and open_cash > 5000:
        order_value(stock, open_cash)
```

技术说明：

  * **买入逻辑** ：根据当前持仓情况和可用资金，决定是否买入未持有的目标股票，并合理分配资金进行开仓。

4\. 市场前准备与目标股票筛选

```python
def before_market_open(context):
    g.pre_holdings = list(context.portfolio.positions)  # 已持仓股票
    # 过滤次新股
    by_date = context.previous_date - timedelta(days=30)
    stock_list = list(get_all_securities(['stock'], date=by_date).index)
    # 过滤ST、停牌，创业板、科创板股票
    current_data = get_current_data()
    stock_list = [code for code in stock_list if not (
            code.startswith(('3', '68', '4', '8'))
            or current_data.is_st
            or current_data.paused
    )]
    # 过滤市值过大的股票
    stock_list = get_fundamentals(
        query(
            valuation.code
        ).filter(
            valuation.code.in_(stock_list),
            valuation.circulating_market_cap < 150
        )
    )['code'].tolist()
    # 选出可能涨停的股票
    g.help_stock = pick_high_limit(context, stock_list)
def pick_high_limit(context, stocks):
    end_date = context.previous_date
    df_pre = get_price(stocks, end_date=end_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False
                       ).query('close < high_limit').set_index('code')
    s_pre_close = df_pre['close']
    stock_list = df_pre.index.tolist()
    df_day_300 = get_price(stock_list, end_date=end_date, frequency='daily',
                           fields=['close'], count=300, panel=False)
    s_high_300 = df_day_300.groupby('code')['close'].apply(lambda x: x.max())
    s_rate_300 = df_day_300.groupby('code')['close'].apply(lambda x: x.max() / x.min() - 1)
    s_high_50 = df_day_300.groupby('code')['close'].apply(lambda x: x[-50:].max())
    s_high_10 = df_day_300.groupby('code')['close'].apply(lambda x: x[-10:].max())
    s_rate_10 = df_day_300.groupby('code')['close'].apply(lambda x: x[-10:].max() / x[-10:].min() - 1)
    target_list = pd.DataFrame(
        {'pre_close': s_pre_close, 'high_300': s_high_300, 'rate_300': s_rate_300,
         'high_50': s_high_50, 'high_10': s_high_10, 'rate_10': s_rate_10
         }
    ).dropna().query(
        'pre_close * 1.2 > high_300 and pre_close * 1.2 > high_50 and pre_close * 1.1 > high_10 and '
        'rate_300 < 2 and rate_10 <= 0.5'
    ).index.tolist()
    dict_high_limit = get_price(target_list, end_date=context.current_dt, fields=['high_limit'],
                                count=1, panel=False).set_index('code')['high_limit'].to_dict()
    return dict_high_limit
```

技术说明：

  * **股票筛选逻辑** ：策略在开盘前会筛选出符合条件的目标股票，这些股票有可能在当天出现涨停，并将其记录下来以便后续操作。

### 策略优势

  * **快速捕捉涨停机会** ：通过严格的筛选条件和实时监控，策略能够迅速捕捉市场中的涨停机会，并在适当的时机进行买入。

  * **精细化的卖出规则** ：多层次的卖出条件确保了在不同的市场情境下，能够及时止盈或止损，最大化收益并有效控制风险。

  * **高效的

资金管理**：通过动态分配资金，确保在最大化利用资金的同时，保持适当的持仓数量，避免过度集中或分散。

### 总结

**动态涨停板追踪与风控策略** 是一种精细化的短线交易策略，通过严格的筛选和实时监控，结合多种卖出条件，实现了对市场涨停机会的有效捕捉和风险控制。该策略适合有较高市场参与度并对短线交易有一定经验的投资者使用，能够在复杂的市场环境中实现较为稳健的收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
