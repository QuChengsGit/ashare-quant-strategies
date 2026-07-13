# 10、稳健价值选股策略

# 策略概述

“稳健价值选股策略”是一种基于基本面数据筛选的量化投资策略，旨在通过优选财务状况健康且具备增长潜力的股票构建投资组合。本策略重视稳健性与分散化，结合财务指标、市场行为以及风险控制手段，在尽可能规避市场风险的前提下，追求长期稳定的收益。

# 策略代码说明

## 1. 初始化函数

**函数名：initialize**

```python
def initialize(context):
    # 系统设置
    log.set_level('order', 'error')  # 过滤低级别日志
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option('avoid_future_data', True)  # 防止未来数据
    set_benchmark('000905.XSHG')  # 设置基准指数为中证500指数
    # 策略参数
    g.stock_num = 95  # 持仓股票数量上限
    # 设定定时运行函数
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(my_Trader, 1, time='9:30')  # 每月初进行调仓
    run_daily(check_limit_up, time='14:00')  # 每日检查涨停股票
```

**说明** ：

  * 本策略在初始化时设置了系统选项、持仓股票数量、基准指数，并设定了定时运行的策略函数。

## 2. 主交易函数

**函数名：my_Trader**

```python
def my_Trader(context):
    # 获取上一个交易日的所有股票列表
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    # 过滤掉科创板、北交所、ST股票
    stocks = filter_kcbj_stock(stocks)
    stocks = filter_st_stock(stocks)
    # 筛选财务指标优秀的股票
    df = get_fundamentals(query(
            valuation.code
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,  # 市净率 > 0
            indicator.inc_return > 0,  # 净资产收益率增长率 > 0
            indicator.inc_total_revenue_year_on_year > 0,  # 营业收入同比增长 > 0
            indicator.inc_net_profit_year_on_year > 0,  # 净利润同比增长 > 0
            indicator.ocf_to_operating_profit > 5  # 经营活动现金流/经营利润 > 5%
        ).order_by(
            valuation.market_cap.asc()  # 按市值升序排序
        ).limit(g.stock_num))  # 限制选股数量
    # 获取最终选择的股票
    choice = list(df.code)
    # 卖出不符合条件的股票
    for stock in context.portfolio.positions:
        if stock not in choice and stock not in g.high_limit_list:
            order_target(stock, 0)
    # 计算每只股票的目标仓位
    psize = context.portfolio.total_value / g.stock_num
    # 买入新的股票
    for stock in choice:
        if context.portfolio.available_cash < psize:
            break
        if stock not in context.portfolio.positions:
            order_value(stock, psize)
```

**说明** ：

  * my_Trader 函数根据财务指标筛选出股票，并按市值从小到大排序后，选出符合条件的股票进行投资。同时，该函数会卖出不再符合选股条件的持仓股票。

## 3. 准备股票池

**函数名：prepare_stock_list**

```python
def prepare_stock_list(context):
    # 获取持仓中昨日涨停的股票
    g.high_limit_list = []
    hold_list = list(context.portfolio.positions)
    if hold_list:
        df = get_price(hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close == high_limit and paused == 0')['code'].tolist()
```

**说明** ：

  * prepare_stock_list 函数会记录持仓中昨日涨停的股票，供后续交易逻辑使用。

## 4. 涨停股票检查

**函数名：check_limit_up**

```python
def check_limit_up(context):
    # 检查持仓股票的涨停情况
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info(f"[{stock}] 涨停打开，卖出")
                order_target(stock, 0)
            else:
                log.info(f"[{stock}] 涨停，继续持有")
```

**说明** ：

  * check_limit_up 函数在每日下午检查持仓中的昨日涨停股票，如果涨停板被打开，则卖出该股票。

## 5. 辅助函数

**科创板和北交所股票过滤** ：

```python
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] == '4' or stock[0] == '8' or stock[:2] == '68')]
```

**ST股票过滤** ：

```python
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
        current_data[stock].is_st or
        'ST' in current_data[stock].name or
        '*' in current_data[stock].name or
        '退' in current_data[stock].name)]
```

**说明** ：

  * filter_kcbj_stock 和 filter_st_stock 函数分别用于过滤掉科创板、北交所的股票以及具有退市风险的ST股票。

# 策略特点

  * **稳健性** ：优选市净率、市盈率和现金流表现优秀的股票，确保组合的财务健康。

  * **分散性** ：持仓最多95只股票，降低个股风险。

  * **动态调整** ：每月定期根据最新的财务数据调整组合，保持组合的优质性。

# 适用场景

本策略适用于风险偏好较低的投资者，希望通过财务指标筛选出具有长期增长潜力的股票，追求稳健收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
