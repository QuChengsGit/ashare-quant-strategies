# 71、资产负债优化选股策略

### 策略介绍

**资产负债优化选股策略** 是一种基于财务健康状况的选股策略。该策略通过多重筛选条件，从全市场中筛选出资产负债率较低、优质资产占比高、ROA（总资产回报率）改善显著的股票，并结合估值指标进行进一步筛选，以构建一个风险较低且增长潜力较大的股票组合。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
def initialize(context):
    # 设置滑点为0.02
    set_slippage(FixedSlippage(0.02))
    # 将国证A指数作为基准
    set_benchmark('399317.XSHE')
    # 使用真实价格交易
    set_option('use_real_price', True)
    # 避免未来数据
    set_option("avoid_future_data", True)
    # 过滤低于error级别的日志
    log.set_level('order', 'error')
    warnings.filterwarnings("ignore")
    # 全局变量设置
    g.stock_num = 10  # 最大持仓数
    g.position = 1  # 仓位比例
    g.bond = '511880.XSHG'  # 债券基金代码
    # 设置交易手续费
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0005, close_commission=0.0005, min_commission=5), type='stock')
    # 每月定期交易
    run_monthly(my_trade, monthday=-4, time='11:30', reference_security='000852.XSHG')
```

技术说明：

  * **滑点设置** ：滑点设为0.02，以模拟真实市场中买卖价差带来的交易成本。

  * **选股数量** ：最大持仓数设置为10，策略会在每次调仓时筛选出10只符合条件的股票。

2\. 选股模块

```python
def get_stock_list(context):
    curr_data = get_current_data()
    yesterday = context.previous_date
    df_stocknum = pd.DataFrame(columns=['当前符合条件股票数量'])
    # 初筛：过滤次新股、ST股、涨跌停股、停牌股
    by_date = yesterday - datetime.timedelta(days=1200)  # 三年内上市股票
    initial_list = get_all_securities(date=by_date).index.tolist()
    initial_list = [stock for stock in initial_list if not (
            (curr_data[stock].day_open == curr_data[stock].high_limit) or
            (curr_data[stock].day_open == curr_data[stock].low_limit) or
            curr_data[stock].paused
    )]
    df_stocknum =  df_stocknum.append({'当前符合条件股票数量': len(initial_list)}, ignore_index=True)
    # 步骤1：筛选出资产负债率由高到低后70%的股票
    df = get_fundamentals(
        query(balance.code, balance.total_liability, balance.total_assets)
        .filter(valuation.code.in_(initial_list))
    ).dropna()
    df['ratio'] = df['total_liability'] / df['total_assets']  # 计算资产负债率
    df = df.sort_values(by='ratio', ascending=False)
    low_liability_list = list(df.code)[int(0.3 * len(df.code)):]
    df_stocknum =  df_stocknum.append({'当前符合条件股票数量': len(low_liability_list)}, ignore_index=True)
    # 步骤2：筛选出不良资产比例适中的股票
    df1 = get_fundamentals(
        query(balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable, balance.other_receivable,
              balance.good_will, balance.intangible_assets, balance.inventories, balance.constru_in_process)
        .filter(balance.code.in_(low_liability_list))
    ).dropna()
    df1['bad_assets'] = df1.sum(axis=1) - df1['total_assets']
    df1['ratio1'] = df1['bad_assets'] / df1['total_assets']
    df1 = df1.sort_values(by='ratio1', ascending=False)
    proper_receivable_list = list(df1.code)[int(0.1 * len(df1.code)):int(0.9 * len(df1.code))]
    df_stocknum =  df_stocknum.append({'当前符合条件股票数量': len(proper_receivable_list)}, ignore_index=True)
    # 步骤3：筛选出优质资产周转率前75%的公司
    df2 = get_fundamentals(
        query(balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable, balance.other_receivable,
              balance.good_will, balance.intangible_assets, balance.inventories, balance.constru_in_process, income.total_operating_revenue)
        .filter(balance.code.in_(proper_receivable_list))
    ).dropna()
    df2['good_assets'] = df2['total_assets'] - (df2.sum(axis=1) - df2['total_assets'] - df2['total_operating_revenue'])
    df2['ratio2'] = df2['total_operating_revenue'] / df2['good_assets']
    df2 = df2.sort_values(by='ratio2', ascending=False)
    proper_receivable_list1 = list(df2.code)[:int(0.75 * len(df2.code))]
    df_stocknum =  df_stocknum.append({'当前符合条件股票数量': len(proper_receivable_list1)}, ignore_index=True)
    # 步骤4：筛选出过去12个季度ROA增长最多的前20%的股票
    df3 = get_history_fundamentals(
        proper_receivable_list1, fields=[indicator.code, indicator.roa], watch_date=yesterday, count=4, interval='1q'
    ).dropna()
    s_delta_avg = df3.groupby('code')['roa'].apply(
        lambda x: x.iloc[3] - x.mean() if len(x) == 4 else 0.0
    ).sort_values(ascending=False)
    roa_list = list(s_delta_avg[:int(0.2 * len(s_delta_avg))].index)
    df_stocknum =  df_stocknum.append({'当前符合条件股票数量': len(roa_list)}, ignore_index=True)
    # 步骤5：从ROA增长量前20%的股票中选出市净率大于0的股票，并按PB升序排列
    pb_list = get_fundamentals(
        query(valuation.code)
        .filter(valuation.code.in_(roa_list), valuation.pb_ratio > 0.7, valuation.ps_ratio < 3)
        .order_by(valuation.pb_ratio.asc())
    )['code'].tolist()
    df_stocknum =  df_stocknum.append({'当前符合条件股票数量': len(pb_list)}, ignore_index=True)
    final_list = pb_list[:g.stock_num]
    return final_list
```

技术说明：

  * **多重财务指标筛选** ：策略通过一系列财务健康指标筛选股票，如资产负债率、不良资产比例、优质资产周转率和ROA增长率，确保选出的股票在财务上表现良好，具有较高的成长潜力。

  * **估值筛选** ：在最终筛选时，根据市净率（PB）进行排序，选择估值相对合理的股票。

3\. 持仓调整模块

```python
def adjust_position(context, buy_stocks):
    # 卖出未在选股列表中的股票
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            order_target(stock, 0)
    # 买入新选出的股票
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

  * **持仓调整** ：策略每月调整一次持仓，先卖出未入选的新股，再按照选股结果买入新的股票，确保投资组合始终由财务健康且具有成长潜力的公司构成。

### 总结

**资产负债优化选股策略** 通过严谨的财务筛选过程，选出资产负债率较低、资产周转率高、ROA增长显著且估值合理的股票，构建一个稳健的投资组合。该策略特别适合于那些希望在控制风险的同时，追求稳健增长的投资者。策略每月定期调整，确保持仓组合的质量和潜在收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
