# 59、分位小盘股动量交易策略

### 策略介绍：

**分位小盘股动量交易策略** 是一种基于量化筛选和动量交易的策略，旨在通过对全市场小盘股进行筛选和分位统计，捕捉小盘股的短期动量机会。策略通过对股票市值、流通股本等因子的筛选，识别出最具增长潜力的小盘股，并动态调整持仓，以求在市场波动中获得稳定的收益。该策略在市场开盘前选定目标股票，在交易时段中根据市场情况进行买卖操作，并定期报告投资组合的表现。

### 核心代码及技术文档说明

1\. 初始化与策略配置

```python
import pandas as pd
from jqdata import *
def initialize(context):
    log.set_level('order', 'error')  # 设置日志输出级别为error
    set_option('use_real_price', True)  # 启用动态复权模式
    set_option('avoid_future_data', True)  # 避免未来数据
    g.days = 0  # 初始化天数计数器
def after_code_changed(context):
    unschedule_all()  # 取消所有之前设定的定时任务
    run_daily(iUpdate, time='before_open')  # 开盘前更新选股池
    run_daily(iTrader, time='9:35')  # 市场开盘后的交易策略
    run_daily(iReport, time='after_close')  # 收盘后报告投资组合情况
```

技术说明：

  * **初始化** ：设置策略的全局参数，包括日志级别、动态复权模式以及避免使用未来数据，确保策略的严谨性和准确性。

  * **定时任务** ：通过 run_daily 函数在开盘前、交易时段和收盘后执行不同的策略模块，确保策略全流程自动化。

2\. 获取指定间隔的交易日

```python
def get_previous_trade_day(current_date, n):
    trade_day = get_trade_days(end_date=current_date, count=n+1)[0]  # 获取距离当前日期 `n` 天前的交易日
    return trade_day
```

技术说明：

  * **获取交易日** ：该函数用于获取指定日期之前的第 n 个交易日，确保策略在回溯历史数据时准确获取交易日信息。

3\. 数据预处理与因子筛选

```python
def drop_outlier(data_list):
    data_list.sort()
    q1 = data_list[int(len(data_list) / 4)]
    q3 = data_list[int(len(data_list) * 3 / 4)]
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    data_list = [x for x in data_list if x >= low and x <= high]  # 去除极值
    return data_list
def divide_list_into_10(data_list):
    data_list.sort()
    chunk_size = len(data_list) // 10
    lst_of_chunks = [data_list[i:i+chunk_size] for i in range(0, len(data_list), chunk_size)]
    result_list = [min(chunk) for chunk in lst_of_chunks]  # 返回每个部分的最小值
    return result_list
def iUpdate(context):
    nchoice = 10  # 选股数量
    nposition = 5  # 持仓数量
    dt_last = context.previous_date
    all_stock = get_all_securities('stock', dt_last)
    # 过滤ST股票和部分板块股票
    cdata = get_current_data()
    stocks = [s for s in all_stock.index if not cdata[s].is_st]
    stocks = [stock for stock in stocks if not stock.startswith('8') and not stock.startswith('688') and not stock.startswith('9')]
    # 获取上一个交易日的日期和因子信息
    previous_trade_day = get_previous_trade_day(context.current_dt, 1)
    valuation_df = get_fundamentals(query(
                valuation.code,
                valuation.turnover_ratio,
                valuation.circulating_cap,
                valuation.capitalization,
                valuation.circulating_market_cap,
                indicator.roe,
                valuation.pe_ratio
            ).filter(
                valuation.code.in_(stocks)
            ), date=previous_trade_day).dropna().set_index('code')
    # 因子处理与筛选
    circulating_cap_factor_list = drop_outlier(valuation_df['circulating_cap'].tolist())
    circulating_cap_factor_list = divide_list_into_10(circulating_cap_factor_list)
    # 筛选小盘股
    df = get_fundamentals(query(
            valuation.code,
            valuation.market_cap,
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,
            valuation.circulating_cap > circulating_cap_factor_list[0],
            valuation.circulating_cap < circulating_cap_factor_list[1],
            indicator.roe > 0,
            indicator.roa > 0.45,
        ).order_by(valuation.market_cap.asc()
        ).limit(nchoice)
    ).dropna().set_index('code')
    g.choice = df.index.tolist()  # 选定的股票列表
    g.position_size = 1.0/nposition * context.portfolio.total_value  # 持仓的目标头寸大小
    print(g.choice)
```

技术说明：

  * **因子筛选与处理** ：通过去除极值和分位统计，将股票的因子数据分为多个部分，筛选出最符合条件的小盘股。

  * **选股逻辑** ：依据市值、流通股本、ROE和ROA等因子筛选出目标股票，并计算每只股票的持仓比例。

4\. 交易逻辑与头寸管理

```python
def iTrader(context):
    choice = g.choice
    position_size = g.position_size
    lm_value = 0.8 * position_size
    hm_value = 1.2 * position_size
    cdata = get_current_data()
    # 卖出不在选股池中的股票
    for s in context.portfolio.positions:
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue
        if s not in choice:
            log.info('sell', s, cdata[s].name)
            order_target(s, 0, MarketOrderStyle(0.99*cdata[s].last_price))
    # 买入或调整仓位
    for s in choice:
        if context.portfolio.available_cash < position_size:
            break
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue
        if s not in context.portfolio.positions:
            log.info('buy', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01*cdata[s].last_price))
        elif context.portfolio.positions[s].value < lm_value:
            log.info('balance+', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01*cdata[s].last_price))
        elif context.portfolio.positions[s].value > hm_value:
            log.info('balance-', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(0.99*cdata[s].last_price))
```

技术说明：

  * **交易逻辑** ：根据市场开盘后的实时数据，对选定的股票进行买入操作，并对已有头寸进行增持或减持操作，确保每只股票的持仓量在合理范围内。

  * **头寸管理** ：根据预设的低值和高值边界对持仓进行平衡，避免单只股票持仓比例过大或过小。

5\. 收盘后报告生成

```python
def iReport(context):
    g.days = g.days + 1
    log.info('positions', len(context.portfolio.positions))
    log.info('return %.2f', 100*context.portfolio.returns)
    log.info('cash %.2f', context.portfolio.available_cash/10000)
    log.info('value %.2f', context.portfolio.total_value/10000)
    log.info('running days', g.days)
```

技术说明：

  * **报告生成** ：在收盘后输出策略的持仓情况、收益情况、现金余额以及总资产等信息，便于投资者了解策略的运行状态和收益情况。

### 策略优势：

  * **小盘股动量捕捉** ：策略通过分位统计和动量筛选，专注于捕捉小盘股的短期增长机会，具有较高的收益潜力。

  * **动态持仓管理** ：策略根据市场变化动态调整持仓，确保投资组合的灵活性和稳定性。

  * **自动化报告** ：收盘后自动生成报告，帮助投资者及时掌握投资组合的表现情况。

### 总结

：

**分位小盘股动量交易策略** 利用分位统计和小盘股的动量特性，通过动态的头寸管理和严格的因子筛选，实现对小盘股市场的精确捕捉。策略适合在市场波动中寻找短期增长机会的投资者，尤其是在小盘股表现活跃的市场环境中，该策略能够提供较好的收益潜力。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
