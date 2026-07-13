# 62、动态选股与风险控制策略

### 策略介绍

**动态选股与风险控制策略** 是一种结合动态选股、持仓管理和风险控制的多功能策略。该策略通过每日筛选优质股票，并根据特定的买卖条件进行交易，以实现最大化收益和控制风险的目标。策略采用了一系列技术指标和规则来决定买入和卖出的时机，同时结合持股天数、收益率等多维度指标进行风险管理。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
from jqdata import *
import datetime as dt
import pandas as pd
def initialize(context):
    # 系统设置
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    log.set_level('system', 'error')
    # 最大持股数
    g.max_hold_num = 5
    g.prepare_stocks = []
    g.chosen_stocks = []  # 每天选出的待买股票
    g.holdable_days = 6  # 可持股天数
    g.hold_days = {}  # 持股天数
    g.need_sell = set()  # 待卖股
    # 调度函数
    run_daily(change_hold_info, time='8:30')
    run_daily(prepare_stocks, '9:05')
    run_daily(market_open, time='every_bar')
    run_daily(do_sell, time='14:40')
    run_daily(do_sell2, time='9:30')
```

技术说明：

  * **初始化** ：策略的初始化函数定义了一系列全局变量，如最大持股数量、待买入股票列表、持股天数等，并设置了每日运行的时间点。

2\. 股票筛选与准备

```python
def prepare_stocks(context):
    if len(context.portfolio.positions) >= g.max_hold_num:
        g.prepare_stocks = []
        log.info("满仓中")
        return
    date = transform_date(context.previous_date, 'str')
    initial_list = prepare_stock_list(date)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(
        valuation.code.in_(initial_list), valuation.circulating_market_cap < 25)
    df = get_fundamentals(q)
    lst = list(df['code'])
    lst = get_hl_stock(lst, date, 300)
    lst = get_no_hl_stock(lst, date, 30)
    lst = filter_amp(lst, date, 15)
    df = upward(lst, date, 15)
    lst = list(df.index)
    lst = approaching_max(lst, date, 60)
    g.prepare_stocks = lst
```

技术说明：

  * **准备股票** ：策略会每天早盘前筛选出初步的股票池，并基于多种条件（如市值、涨停等）进一步过滤，最终生成当天待买入的股票列表。

3\. 买入与卖出决策

```python
def do_sell(context):
    if len(context.portfolio.positions) < 1:
        log.info("空仓没什么可卖的")
        return
    pos = context.portfolio.positions
    for stock in pos:
        if pos[stock].closeable_amount <= 0:
            continue
        if is_limitup(stock):
            log.info("%s 涨停的不卖" % stock)
            continue
        if stock in g.chosen_stocks:
            log.info("%s 还在选股范围内的不卖" % stock)
            continue
        if check_earn(pos[stock], 12) and scream_sell(stock, context.current_dt + dt.timedelta(minutes=-10), pos[stock].price):
            log.info("卖出{}, scream_sell".format(stock))
            g.need_sell.add(stock)
        if check_hold_days(pos[stock]):
            log.info("卖出{}, check_hold_days".format(stock))
            g.need_sell.add(stock)
        if big_volume_sell(stock, pos[stock].price, context):
            log.info("卖出{}, big_volume_sell".format(stock))
            g.need_sell.add(stock)
        if check_earn(pos[stock], 15):
            log.info("卖出{}, check_earn".format(stock))
            g.need_sell.add(stock)
    for stock in g.need_sell.copy():
        if close_position(pos[stock]):
            g.need_sell.remove(stock)
```

技术说明：

  * **卖出逻辑** ：策略结合涨停、盈利、持股天数等多维度的指标，动态判断是否需要卖出持仓中的股票，并在一定条件下执行卖出操作。

4\. 交易执行

```python
def do_buy(context):
    hold_num = len(context.portfolio.positions)
    if hold_num >= g.max_hold_num:
        log.info("满仓中")
        return
    holdable_num = g.max_hold_num - hold_num
    cash = context.portfolio.available_cash / holdable_num
    chosen_stocks = g.chosen_stocks
    current_data = get_current_data()
    for stock in chosen_stocks:
        if stock in context.portfolio.positions:
            log.info("不买已经持有的股票%s" % stock)
            continue
        if stock in g.need_sell:
            log.info("不买满足卖出条件没有卖出的股票%s" % stock)
            continue
        if ((context.portfolio.positions[stock].closeable_amount != 0) and (current_data[stock].last_price < current_data[stock].high_limit)):
            log.info("已经涨停无法买入%s" % stock)
            continue
        if open_position(stock, cash):
            if len(context.portfolio.positions) >= g.max_hold_num:
                break
```

技术说明：

  * **买入逻辑** ：策略在满足一定条件的情况下执行买入操作，确保不会买入已经涨停或持有的股票，并动态调整持仓。

5\. 风险管理与辅助函数

```python
def add_hold_info(stock):
    g.hold_days[stock] = 0
def del_hold_info(stock):
    g.hold_days.pop(stock)
def change_hold_info(context):
    for stock in g.hold_days.keys():
        g.hold_days[stock] += 1
        log.info("%s 持股天数%s" % (stock, g.hold_days[stock]))
```

技术说明：

  * **持仓管理** ：通过记录并更新每只股票的持仓天数，策略能够动态调整并及时止盈或止损，减少风险。

### 策略优势：

  * **多维筛选与动态调整** ：结合多种技术指标与条件进行动态筛选和调整，确保选出的股票在当前市场环境中具有较高的潜力。

  * **多重风险控制** ：通过持股天数、涨跌停、成交量等多维度的风险控制，策略能有效管理风险，防止过早或过晚的买卖操作。

  * **灵活交易机制** ：策略根据市场变化灵活调整买卖决策，确保在市场波动中保持较高的交易灵敏度。

### 总结：

**动态选股与风险控制策略** 是一种集成了多种量化分析方法与风险管理手段的投资策略。该策略通过严格的选股与动态调整机制，力求在复杂的市场环境中获取稳定的投资回报，并通过多重风险控制措施保护投资组合的安全性。策略适合希望在市场中灵活应对风险并寻求稳健增长的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
