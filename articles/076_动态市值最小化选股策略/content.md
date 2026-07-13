# 76、动态市值最小化选股策略

# 策略概述

**动态市值最小化选股策略** 是一种基于市值筛选的选股策略，通过每周筛选市值较小的股票，并结合动态的止损机制，以控制风险并最大化收益。策略利用沪深300指数作为基准，每周筛选沪深300指数和深证成份股中市值最小的股票，并按固定数量分配持仓。策略核心是市值因子，利用市值较小的股票在市场中可能获得的高收益潜力，同时通过动态止损来保护资金安全。

### 核心功能代码

```python
from jqdata import *
# 初始化函数
def initialize(context):
    # 设置持股数量
    g.stocknum = 10
    # 初始化待买入股票列表
    g.buylist = []
    # 设置沪深300股指作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式（使用真实价格）
    set_option('use_real_price', True)
    # 交易量不超过实际成交量的 10%
    set_option('order_volume_ratio', 0.1)
    # 设置滑点（0.02 的滑点）
    set_slippage(FixedSlippage(0.02))
    # 设置交易费用
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 过滤掉 order 系列 API 产生的比 error 级别低的日志
    log.set_level('order', 'error')
    # 设置定时任务
    run_daily(stoploss, '9:45')  # 止损函数
    run_weekly(filter_stocks, 1, '09:30')  # 每周一筛选股票
    run_weekly(market_open, 1, '10:00')  # 每周一进行调仓
# 筛选、排序股票，生成待交易股票列表
def filter_stocks(context):
    log.info(f'函数运行时间（filter_stocks）: {context.current_dt.time()}')
    # 获取当前的市场数据
    curr_data = get_current_data()
    # 获取上证综指和深证综指的成份股
    stock_universe = get_index_stocks('000001.XSHG') + get_index_stocks('399106.XSHE')
    # 过滤开盘涨停、跌停、暂停交易及ST、退市股票
    stock_universe = [stock for stock in stock_universe if not (
            (curr_data[stock].day_open == curr_data[stock].high_limit) or
            (curr_data[stock].day_open == curr_data[stock].low_limit) or
            curr_data[stock].paused or
            ('ST' in curr_data[stock].name) or
            ('*' in curr_data[stock].name) or
            ('退' in curr_data[stock].name)
    )]
    # 获取市值最小的股票列表
    q = query(valuation.code, valuation.market_cap).filter(
        valuation.code.in_(stock_universe)).order_by(
        valuation.market_cap.asc()).limit(g.stocknum)
    # 获取前一个交易日的股票数据
    df = get_fundamentals(q, date=context.previous_date)
    # 将待买入股票列表赋值给全局变量
    g.buylist = list(df['code'])
# 止损函数
def stoploss(context):
    for stock in context.portfolio.positions:
        cost = context.portfolio.positions[stock].avg_cost
        price = context.portfolio.positions[stock].price
        ret = price / cost - 1
        # 如果亏损超过 20%，执行止损
        if ret < -0.2:
            order_target(stock, 0)
            log.info(f'触发止损，卖出 {stock}')
# 开盘时运行函数
def market_open(context):
    log.info(f'函数运行时间（market_open）: {context.current_dt.time()}')
    if not g.buylist:
        return
    # 调整持仓
    rebalance(context, g.buylist)
# 调仓函数
def rebalance(context, buylist):
    every_stock = context.portfolio.portfolio_value / len(buylist)
    # 如果没有持仓，直接均等买入
    if not context.portfolio.positions:
        for stock_to_buy in buylist:
            order_target_value(stock_to_buy, every_stock)
    else:
        # 先卖出不在买入列表中的股票
        for stock_to_sell in list(context.portfolio.positions.keys()):
            if stock_to_sell not in buylist:
                order_target_value(stock_to_sell, 0)
        # 调整持仓中的股票，重新分配仓位
        for stock in buylist:
            order_target_value(stock, every_stock)
```

### 技术文档说明

1\. 策略初始化 (initialize)

  * **功能** : 初始化策略的全局参数，设置基准、滑点、交易成本等，并安排定时任务。

  * **关键配置** :

    * set_benchmark('000300.XSHG'): 设置沪深300为基准指数。

    * set_slippage(FixedSlippage(0.02)): 设置固定滑点为0.02。

    * set_order_cost(OrderCost(...), type='stock'): 设置股票的交易费用。

2\. 股票筛选函数 (filter_stocks)

  * **功能** : 每周一筛选市值最小的股票，生成待买入股票列表。

  * **逻辑** :

    * 通过过滤涨停、跌停、停牌、ST及退市股票，保证筛选出的股票具有较好的流动性和安全性。

    * 筛选出市值最小的10只股票，并将其加入待买入股票列表。

3\. 止损函数 (stoploss)

  * **功能** : 每日检查持仓股票的收益情况，若亏损超过20%，则执行止损卖出。

  * **逻辑** :

    * 根据每只股票的当前价格与成本价的比较，如果亏损超过20%，则立即清仓卖出。

4\. 开盘调仓函数 (market_open)

  * **功能** : 每周一开盘后对股票进行调仓，买入符合条件的股票，卖出不在待买入列表中的股票。

  * **逻辑** :

    * 如果待买入列表不为空，则调用rebalance函数进行调仓操作。

5\. 调仓函数 (rebalance)

  * **功能** : 根据当前持仓情况和待买入股票列表，进行调仓操作。

  * **逻辑** :

    * 首先卖出不在待买入列表中的持仓股票，然后对待买入列表中的股票进行均等分配资金进行买入或调整仓位。

### 策略亮点

  * **市值筛选** : 策略核心基于市值因子，优先选择市值较小的股票，利用其潜在的高增长机会。

  * **动态调仓** : 每周一动态筛选和调仓，确保投资组合始终具有较好的成长性。

  * **止损机制** : 设立20%的止损线，保护投资组合的下行风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
