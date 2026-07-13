# 2、多因子综合评分量化策略

# 1. 概述

该量化交易策略通过筛选股票并进行周频调仓来实现投资目标。策略核心是根据多个因子构建股票池，并通过计算得分筛选优质股票。策略包含了基础的风险控制机制，如过滤停牌股票、ST股票、涨跌停股票等。策略每周调整持仓，并动态调整持有股票。



# 2. 代码结构概览

  * **初始化函数** (initialize): 设置策略的基础配置，包括基准、交易参数、初始化全局变量、以及定时任务。

  * **准备股票池** (prepare_stock_list): 每日生成当前持仓股票列表和昨日涨停股票列表。

  * **选股模块** (get_stock_list): 根据因子计算和排序，筛选出符合条件的股票。

  * **整体调整持仓** (weekly_adjustment): 每周根据选股结果调整持仓，卖出不符合条件的股票，买入新股票。

  * **检查涨停股票** (check_limit_up): 检查昨日涨停股票是否继续涨停，否则卖出。

  * **过滤模块** ：提供多种过滤函数，用于过滤停牌、ST、涨跌停、科创板、次新股等。

  * **交易模块** ：包括自定义下单、开仓、平仓、调仓等功能。

  * **日志与调试** ：打印持仓信息及交易记录，方便调试和跟踪策略运行情况。



# 3. 详细代码解释

## 3.1 初始化函数 (initialize)

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设定基准为中证500指数
    set_option('use_real_price', True)  # 用真实价格交易
    set_option("avoid_future_data", True)  # 启用防未来数据
    set_slippage(PriceRelatedSlippage(0.000))  # 设置理想滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    g.stock_num = 50  # 目标持仓股票数量
    g.limit_up_list = []  # 涨停股票列表
    g.hold_list = []  # 当前持仓列表
    g.weights = [1.0, 1.0, 1.6, 0.8, 2.0]  # 各因子的权重
    # 设置交易时间和任务调度
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

该函数设置策略的初始状态，包括基准、滑点、交易成本等。并定义了全局变量如 g.stock_num 和 g.weights，以便后续策略的计算和调整。此外，还通过 run_daily 和 run_weekly 设置了每日和每周需要运行的任务。

## 3.2 股票池准备函数 (prepare_stock_list)

```python
def prepare_stock_list(context):
    g.hold_list= []
    for position in list(context.portfolio.positions.values()):
        g.hold_list.append(position.security)
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.high_limit_list = []
```

该函数用于每天准备当前持仓列表，并检查哪些股票昨日涨停。如果持仓中有股票昨日涨停，则将其加入 g.high_limit_list 以供后续决策使用。

## 3.3 选股模块 (get_stock_list)

```python
def get_stock_list(context):
    ...
    # 获得初始列表
    yesterday = context.previous_date
    initial_list = get_all_securities('stock', yesterday).index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_new_stock(context, initial_list, 375)
    initial_list = filter_st_stock(initial_list)
    # 使用财务指标过滤股票
    q = query(
        valuation.code, valuation.market_cap, valuation.circulating_market_cap
    ).filter(
        valuation.code.in_(initial_list),
        valuation.pb_ratio > 0,
        indicator.inc_return > 0,
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0
    ).order_by(valuation.market_cap.asc()).limit(100)
    df = get_fundamentals(q, date=yesterday)
    # 计算得分并排序
    ...
    df['score'] = temp_list
    df = df.sort_values(by='score', ascending=False)
    return list(df.index)
```

选股模块通过筛选多个因子，包括总市值、流通市值、成交量、涨幅等，计算每只股票的综合得分并排序，最后返回得分最高的股票列表。这里用到了多个自定义过滤函数，如 filter_kcbj_stock 和 filter_st_stock，以过滤科创板和ST股票。

## 3.4 持仓调整函数 (weekly_adjustment)

```python
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    target_list = target_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
            log.info(f"卖出[{stock}]")
            close_position(context.portfolio.positions[stock])
        else:
            log.info(f"已持有[{stock}]")
    position_count = len(context.portfolio.positions)
    if len(target_list) > position_count:
        value = context.portfolio.cash / (len(target_list) - position_count)
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == len(target_list):
                        break
```

每周一执行持仓调整，根据最新的选股结果卖出不符合条件的股票，并买入新选出的股票。对于涨停未打开的股票，即使不在目标股票列表中，也暂时持有。

## 3.5 过滤与交易模块

该部分代码提供了一些辅助函数用于过滤不合格的股票（如停牌、ST、涨跌停等），以及执行交易的函数（如开仓、平仓、调仓等）。

## 3.6 打印持仓信息 (print_position_info)

```python
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：'+str(_trade))
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print(f'代码:{securities}')
        print(f'成本价:{format(cost, ".2f")}')
        print(f'现价:{price}')
        print(f'收益率:{format(ret, ".2f")}%')
        print(f'持仓(股):{amount}')
        print(f'市值:{format(value, ".2f")}')
        print('———————————————————————————————————')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
```

该函数打印当前持仓的详细信息，包括股票代码、成本价、现价、收益率、持仓量和市值等，方便用户在每日交易结束后查看持仓情况。



# 4. 策略优化建议

  1. **因子权重优化** ：可以考虑引入机器学习模型或遗传算法对因子权重进行动态优化，以提高选股的准确性。

  2. **多因子策略组合** ：通过引入更多不同类型的因子（如动量、基本面、市场情绪等），构建更加全面的多因子模型。

  3. **分散投资** ：可适当增加持仓股票数量，降低个股风险。

  4. **止损机制** ：引入止损功能，防止单一股票带来的极端风险。



该文档为策略代码提供了详细的技术解释及使用指导。通过结合不同因子和过滤条件，策略力图在捕捉市场机会的同时控制风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
