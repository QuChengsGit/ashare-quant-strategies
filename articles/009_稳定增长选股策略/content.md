# 9、稳定增长选股策略

### 1. 策略概述

“稳定增长选股策略”是一种基于财务指标和基本面分析的量化策略，旨在从市场中筛选出一组具有良好财务表现、增长稳定的股票进行投资。策略通过定期筛选股票并调整持仓，确保组合中的股票具有较高的盈利能力和稳健的市场表现。

### 2. 策略代码

```python
import pandas as pd
def initialize(context):
    # 系统设置
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_benchmark('000905.XSHG')
    # 策略参数
    g.stock_num = 95  # 持仓股票数量
    # 设置策略运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(my_Trader, 1, time='9:30')
    run_daily(check_limit_up, time='14:00')
# 主交易函数：每月进行调仓操作
def my_Trader(context):
    # 获取所有股票列表
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    # 过滤科创板和北交所股票以及ST股票
    stocks = filter_kcbj_stock(stocks)
    stocks = filter_st_stock(stocks)
    # 获取基本面数据并筛选
    df = get_fundamentals(query(
            valuation.code
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,
            indicator.inc_return > 0,
            indicator.inc_total_revenue_year_on_year > 0,
            indicator.inc_net_profit_year_on_year > 0,
            indicator.ocf_to_operating_profit > 5
        ).order_by(
            valuation.market_cap.asc()
        ).limit(g.stock_num))
    choice = list(df.code)
    # 卖出不在选择列表中的股票
    for stock in context.portfolio.positions:
        if stock not in choice and stock not in g.high_limit_list:
            order_target(stock, 0)
    # 计算每只股票的买入金额并买入新股票
    psize = context.portfolio.total_value / g.stock_num
    for stock in choice:
        if context.portfolio.available_cash < psize:
            break
        if stock not in context.portfolio.positions:
            order_value(stock, psize)
# 准备股票池，记录涨停股票
def prepare_stock_list(context):
    g.high_limit_list = []
    hold_list = list(context.portfolio.positions)
    if hold_list:
        df = get_price(hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close == high_limit and paused == 0')['code'].tolist()
# 调整昨日涨停股票的持仓情况
def check_limit_up(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info(f"[{stock}]涨停打开，卖出")
                order_target(stock, 0)
            else:
                log.info(f"[{stock}]涨停，继续持有")
# 过滤科创板和北交所股票
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] == '4' or stock[0] == '8' or stock[:2] == '68')]
# 过滤ST及其他具有退市标签的股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
        current_data[stock].is_st or
        'ST' in current_data[stock].name or
        '*' in current_data[stock].name or
        '退' in current_data[stock].name)]
```

### 3. 策略说明

3.1 策略逻辑

  * **基本面筛选** ：通过筛选市净率（PB Ratio）、收益增长率、营业收入同比增长率、净利润同比增长率、经营性现金流净利润占比等多个财务指标，选出财务健康、增长稳定的股票。

  * **调仓机制** ：每月定期进行调仓，剔除不符合条件的股票，并按市值由低到高进行排序，从而分散投资风险。

  * **风险控制** ：通过剔除科创板、北交所、ST股等高风险股票，保证组合的稳健性。

3.2 交易机制

  * **调仓周期** ：每月初根据最新的财务数据进行调仓。

  * **持仓管理** ：始终保持最多持有95只股票，仓位平衡且分散。

### 4. 策略特点

  * **稳健性** ：优选稳定增长的股票，追求长期稳健收益。

  * **分散化** ：通过持有多只股票分散风险，防止单一股票对组合造成较大波动。

  * **自动调仓** ：每月自动调仓，确保组合始终由表现最佳的股票构成。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
