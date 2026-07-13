# 60、高质量资产筛选与动量配置策略

### 策略介绍：

**高质量资产筛选与动量配置策略** 是一种基于财务指标筛选和动态调整仓位的量化交易策略。该策略旨在通过严格筛选出资产负债率低、不良资产率适中、优质资产周转率高、ROA（资产收益率）增长显著的股票，并依据市净率（PB）等估值指标优化组合，动态配置持仓。策略主要适用于稳健型投资者，通过每月调仓实现对高质量资产的有效配置，力求在市场中获得长期稳定的回报。

### 核心代码及技术文档说明

1\. 初始化函数

```python
from jqdata import *
import warnings
def initialize(context):
    set_slippage(FixedSlippage(0.02))  # 设置固定滑点
    set_benchmark('000300.XSHG')  # 设置基准指数为沪深300
    set_option('use_real_price', True)  # 开启动态复权模式
    set_option('avoid_future_data', True)  # 避免未来数据
    log.set_level('order', 'error')  # 设置日志输出级别为error
    warnings.filterwarnings('ignore')  # 过滤警告信息
    # 全局变量设置
    g.stock_num = 5  # 最大股票持仓数量
    g.position = 1  # 仓位比例
    # 设置交易时间，每月第一个交易日执行交易函数
    run_monthly(my_trade, monthday=1, time='10:00', reference_security='000300.XSHG')
```

技术说明：

  * **初始化** ：在初始化函数中设置策略的基础配置，包括滑点、基准指数、动态复权模式、日志级别等。全局变量用于定义策略的持仓数量和仓位比例。

  * **交易时间设置** ：通过 run_monthly 函数设定每月的调仓时间，确保策略按时执行交易操作。

2\. 交易函数

```python
def my_trade(context):
    check_out_list = get_stock_list(context)  # 获取待买入股票列表
    log.info('今日准备购买的股票:%s' % check_out_list)  # 输出待买入的股票列表
    adjust_position(context, check_out_list)  # 调整持仓
```

技术说明：

  * **交易函数** ：该函数主要调用选股模块获取当日符合条件的股票列表，并根据该列表调整持仓，卖出不再持仓列表中的股票，买入新选出的股票。

3\. 选股模块

```python
def get_stock_list(context):
    curr_data = get_current_data()  # 获取当前行情数据
    yesterday = context.previous_date  # 获取前一个交易日的日期
    # 初步筛选符合条件的股票列表
    by_date = yesterday - datetime.timedelta(days=1200)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 过滤次新股、ST、停牌、涨跌停股票
    initial_list = [stock for stock in initial_list if not (
        (curr_data[stock].day_open == curr_data[stock].high_limit) or
        (curr_data[stock].day_open == curr_data[stock].low_limit) or
        curr_data[stock].paused or
        ('ST' in curr_data[stock].name) or
        ('*' in curr_data[stock].name) or
        ('退' in curr_data[stock].name)
    )]
    # 筛选资产负债率较低的股票
    df = get_fundamentals(query(
            balance.code, balance.total_liability, balance.total_assets
        ).filter(
            valuation.code.in_(initial_list)
        )
    ).dropna()
    df['ratio'] = df['total_liability'] / df['total_assets']
    df = df.sort_values(by='ratio', ascending=False)
    low_liability_list = list(df.code)[int(0.3*len(df.code)):]
    # 筛选不良资产率适中的股票
    df1 = get_fundamentals(query(
            balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
            balance.other_receivable, balance.good_will, balance.intangible_assets,
            balance.inventories, balance.constru_in_process
        ).filter(
            balance.code.in_(low_liability_list)
        )
    ).dropna()
    df1['bad_assets'] = df1.sum(axis=1) - df1['total_assets']
    df1['ratio1'] = df1['bad_assets'] / df1['total_assets']
    df1 = df1.sort_values(by='ratio1', ascending=False)
    proper_receivable_list = list(df1.code)[int(0.1*len(df1.code)):int(0.9*len(df1.code))]
    # 筛选优质资产周转率较高的股票
    df2 = get_fundamentals(query(
            balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
            balance.other_receivable, balance.good_will, balance.intangible_assets,
            balance.inventories, balance.constru_in_process, income.total_operating_revenue
        ).filter(
            balance.code.in_(proper_receivable_list)
        )
    ).dropna()
    df2['good_assets'] = df2['total_assets'] - (df2.sum(axis=1) - df2['total_assets'] - df2['total_operating_revenue'])
    df2['ratio2'] = df2['total_operating_revenue'] / df2['good_assets']
    df2 = df2.sort_values(by='ratio2', ascending=False)
    proper_receivable_list1 = list(df2.code)[:int(0.75*len(df2.code))]
    # 筛选ROA增长显著的股票
    df3 = get_history_fundamentals(
        proper_receivable_list1, fields=[indicator.code, indicator.roa],
        watch_date=yesterday, count=4, interval='1q'
    ).dropna()
    s_delta_avg = df3.groupby('code')['roa'].apply(
        lambda x: x.iloc[3] - x.mean() if len(x) == 4 else 0.0
    ).sort_values(ascending=False)
    roa_list = list(s_delta_avg[:int(0.2*len(s_delta_avg))].index)
    # 筛选市净率较低的股票并生成最终买入列表
    pb_list = get_fundamentals(query(
        valuation.code
    ).filter(
        valuation.code.in_(roa_list),
        valuation.pb_ratio > 0.7,
        valuation.ps_ratio < 3
    ).order_by(
        valuation.pb_ratio.asc()
    ))['code'].tolist()
    final_list = pb_list[:g.stock_num]
    return final_list
```

技术说明：

  * **选股模块** ：该模块通过一系列财务指标（如资产负债率、不良资产率、优质资产周转率、ROA增长、市净率等）进行筛选和排序，最终生成符合条件的股票列表。

  * **多重筛选** ：通过多层筛选确保选出的股票具有较好的财务健康状况，并在估值上具有较好的性价比。

4\. 仓位调整模块

```python
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            order_target(stock, 0)  # 卖出不在买入列表中的股票
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash * g.position / (g.stock_num - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                order_target_value(stock, value)
                if len(context.portfolio.positions) == g.stock_num:
                    break
```

技术说明：

  * **仓位调整** ：根据选出的买入列表动态调整仓位，卖出不符合条件的股票，买入新选出的股票，确保持仓数量和组合风险控制在合理范围内。

### 策略优势：

  * **高质量选股** ：通过多层财务指标筛选出具有良好资产质量和增长潜力的股票，确保投资组合的整体质量。

  * **动量配置** ：策略结合了动量因子和估值因子，动态调整仓位，实现资产的有效配置。

  * **自动化管理** ：策略每月自动执行，减轻了人工操作的负担，保持投资纪律性。

### 总结：

**高质量资产筛选与动量配置策略** 是一套稳健的量化策略，适合追求长期稳定回报的投资者。策略通过严格的财务指标筛选和动态仓位管理，确保在波动市场中保持投资组合的高质量和低风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
