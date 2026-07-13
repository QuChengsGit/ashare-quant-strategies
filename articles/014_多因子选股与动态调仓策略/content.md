# 14、多因子选股与动态调仓策略

# 策略概述

该策略名为“多因子选股与动态调仓策略”，采用多因子模型进行选股，并结合涨停、跌停、停牌等因素动态调仓。策略通过定期筛选优质股票并执行调仓操作，力求在控制风险的前提下，实现稳定的投资收益。策略对部分特殊情况（如清仓条件）进行了处理，保证资金安全。

# 策略优化与详细代码说明

## 1. 初始化函数

**函数名：initialize**

```python
def initialize(context):
    # 设置系统参数
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_benchmark('000300.XSHG')
    # 设置交易参数
    set_slippage(FixedSlippage(0.02))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    # 初始化全局变量
    g.no_trading_today_signal = False
    g.stock_num = 10
    g.choice = []
    g.just_sold = []
    g.limit_days = 30
    g.hold_list = []
    g.history_hold_list = []
    g.not_buy_again_list = []
    # 调度任务
    run_daily(prepare_high_limit_list, time='9:05', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00')
    run_monthly(my_Trader, -1, time='9:30', force=True)
    run_monthly(go_Trader, -1, time='14:55', force=True)
    run_daily(close_account, '14:30')
```

**说明** ：

  * 初始化函数设置了日志级别、基准、交易滑点和成本等参数。

  * 策略调度了日内、每月的选股、调仓以及每日检查涨停股票、清仓等任务。

## 2. 选股与调仓函数

**函数名：my_Trader**

```python
def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    choice = filter_st_stock(stocks)
    choice = filter_paused_stock(choice)
    choice = filter_new_stock(context, choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    choice = get_peg(context, choice)
    recent_limit_up_list = get_recent_limit_up_stock(context, choice, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in choice if stock not in black_list]
    choice = target_list[:min(g.stock_num, len(target_list))]
    g.choice = choice[:g.stock_num]
```

**说明** ：

  * 该函数通过一系列过滤条件筛选股票池，并通过PEG等基本面指标进一步筛选出具有投资价值的股票。

  * 最终选出的股票存入g.choice，供后续调仓使用。

**函数名：go_Trader**

```python
def go_Trader(context):
    if g.no_trading_today_signal == False:
        cdata = get_current_data()
        choice = g.choice
        for s in context.portfolio.positions:
            if s not in choice and not cdata[s].paused:
                log.info('Sell', s, cdata[s].name)
                order_target(s, 0)
                g.just_sold.append(s)
                if len(g.just_sold) >= g.limit_days:
                    g.just_sold = g.just_sold[-g.stock_num:]
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count:
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in choice:
                if s not in context.portfolio.positions:
                    log.info('Buy', s, cdata[s].name)
                    order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break
```

**说明** ：

  * go_Trader函数每月执行一次，根据选股结果进行调仓操作，先卖出不再持有的股票，再根据可用资金买入新选出的股票。

## 3. 涨停股票处理

**函数名：prepare_high_limit_list**

```python
def prepare_high_limit_list(context):
    g.high_limit_list = []
    hold_list = list(context.portfolio.positions)
    if hold_list:
        df = get_price(hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False)
        g.high_limit_list = df[df['close'] == df['high_limit']]['code'].tolist()
    g.no_trading_today_signal = False
    g.hold_list = []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        for stock in hold_list:
            temp_set.add(stock)
    g.not_buy_again_list = list(temp_set)
```

**说明** ：

  * 该函数准备昨日涨停且正在持有的股票列表，并更新不再买入的股票黑名单，以避免重复买入。

**函数名：check_limit_up**

```python
def check_limit_up(context):
    if g.no_trading_today_signal == False:
        current_data = get_current_data()
        if g.high_limit_list:
            for stock in g.high_limit_list:
                if current_data[stock].last_price < current_data[stock].high_limit:
                    order_target(stock, 0)
                    log.info("[%s]涨停打开，卖出" % stock)
                    g.just_sold.append(stock)
                    if len(g.just_sold) >= g.limit_days:
                        g.just_sold = g.just_sold[-g.stock_num:]
                else:
                    log.info("[%s]涨停，继续持有" % stock)
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count and position_count != 0:
            my_Trader(context)
            cdata = get_current_data()
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in g.choice:
                if s not in context.portfolio.positions:
                    order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break
```

**说明** ：

  * 该函数监控涨停股票，并在涨停打开时卖出，同时保证持仓数量符合策略配置。

## 4. 其他辅助函数

  * filter_kcbj_stock、filter_st_stock、filter_paused_stock、filter_limitup_stock、filter_limitdown_stock、filter_highprice_stock等函数用于实现股票筛选。

  * get_peg函数用于根据基本面因子筛选并排序股票。

### 策略适用场景

该策略适用于稳健型投资者，通过多因子选股模型进行筛选，并结合动态调仓与涨停股票的处理，力求在控制风险的前提下实现稳定收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
