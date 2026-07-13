# 92、低负债高周转多因子选股策略

# 策略概述

**低负债高周转多因子选股策略** 是一种基于多因子分析的量化交易策略，主要目标是筛选出具有低负债率、高资产周转率且ROA（资产回报率）显著改善的优质股票进行投资。该策略通过分阶段筛选股票池，最终选择出符合严格财务指标要求的股票构建投资组合，并动态调整持仓以适应市场变化。

# 策略详细介绍

  1. **策略思想** ：

     * **多因子筛选** ：策略首先通过一系列财务指标（如资产负债率、资产周转率、ROA等）筛选出潜在的优质股票，剔除不符合条件的公司。

     * **动量分析** ：在最终选股时，考虑股票的周期动量指标，通过BBI指标进一步筛选并优化股票池。

     * **动态调仓** ：根据策略设定的调仓周期，定期更新股票池并进行仓位调整。

  2. **关键要素** ：

     * **低负债筛选** ：通过资产负债率过滤掉负债率过高的公司，确保公司的财务稳定性。

     * **优质资产周转** ：选择资产周转率高的公司，表明公司具备良好的运营效率。

     * **ROA改善筛选** ：关注ROA显著提升的公司，表明公司盈利能力正在改善。

     * **动量优化** ：利用BBI指标进行动量分析，筛选出具有较好市场表现的股票。

# 策略代码与功能说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    set_slippage(FixedSlippage(0.02))  # 设置滑点
    set_benchmark('399317.XSHE')  # 设定国证A指数作为基准
    set_option('use_real_price', True)  # 开启真实价格交易
    set_option("avoid_future_data", True)  # 避免未来数据
    log.set_level('order', 'error')  # 设置日志级别
    warnings.filterwarnings("ignore")  # 忽略警告
    g.stock_num = 10  # 持仓股票数
    g.position = 1  # 仓位
    g.bond = '511880.XSHG'  # 债券标的
    # 设置交易成本
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0005, close_commission=0.0005, min_commission=5), type='stock')
    # 每月定期调仓
    run_monthly(my_trade, monthday=-4, time='11:30', reference_security='000852.XSHG')
```

  * **功能说明** : 初始化策略的各项参数，包括滑点、基准、仓位设置、交易成本和调仓周期。

  * **关键逻辑** :

    * run_monthly 函数用于设置策略每月的调仓操作，确保股票池和持仓结构能够及时更新。

2\. 选股函数 (get_stock_list)

```python
def get_stock_list(context):
    curr_data = get_current_data()
    yesterday = context.previous_date
    df_stocknum = pd.DataFrame(columns=['当前符合条件股票数量'])
    by_date = yesterday - datetime.timedelta(days=1200)  # 三年
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 0. 过滤创业板、科创板、ST股等
    initial_list = [stock for stock in initial_list if not (
            curr_data[stock].day_open == curr_data[stock].high_limit or
            curr_data[stock].day_open == curr_data[stock].low_limit or
            curr_data[stock].paused
    )]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(initial_list)}, ignore_index=True)
    # 1. 资产负债率由高到低后70%
    df = get_fundamentals(query(
        balance.code, balance.total_liability, balance.total_assets
    ).filter(
        valuation.code.in_(initial_list)
    )).dropna()
    df['ratio'] = df['total_liability'] / df['total_assets']
    df = df.sort_values(by='ratio', ascending=False)
    low_liability_list = list(df.code)[int(0.3*len(list(df.code))):]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(low_liability_list)}, ignore_index=True)
    # 2. 选出不良资产比率在总体中[20%-80%]范围内的股票
    df1 = get_fundamentals(query(
        balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
        balance.other_receivable, balance.good_will, balance.intangible_assets,
        balance.inventories, balance.constru_in_process
    ).filter(
        balance.code.in_(low_liability_list)
    )).dropna()
    df1['bad_assets'] = df1.sum(axis=1) - df1['total_assets']
    df1['ratio1'] = df1['bad_assets'] / df1['total_assets']
    df1 = df1.sort_values(by='ratio1', ascending=False)
    proper_receivable_list = list(df1.code)[int(0.1*len(list(df1.code))):int(0.9*len(list(df1.code)))]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(proper_receivable_list)}, ignore_index=True)
    # 3. 优质资产周转率前75%的公司
    df2 = get_fundamentals(query(
        balance.code, balance.total_assets, balance.bill_receivable, balance.account_receivable,
        balance.other_receivable, balance.good_will, balance.intangible_assets,
        balance.inventories, balance.constru_in_process, income.total_operating_revenue
    ).filter(
        balance.code.in_(proper_receivable_list)
    )).dropna()
    df2['good_assets'] = df2['total_assets'] - (df2.sum(axis=1) - df2['total_assets'] - df2['total_operating_revenue'])
    df2['ratio2'] = df2['total_operating_revenue'] / df2['good_assets']
    df2 = df2.sort_values(by='ratio2', ascending=False)
    proper_receivable_list1 = list(df2.code)[:int(0.75*len(list(df2.code)))]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(proper_receivable_list1)}, ignore_index=True)
    # 4. 过去四个季度ROA增长最多(前20%)的股票
    df3 = get_history_fundamentals(
        proper_receivable_list1,
        fields=[indicator.code, indicator.roa],
        watch_date=yesterday,
        count=4,
        interval='1q'
    ).dropna()
    s_delta_avg = df3.groupby('code')['roa'].apply(
        lambda x: x.iloc[3] - x.mean() if len(x) == 4 else 0.0
    ).sort_values(ascending=False)
    roa_list = list(s_delta_avg[:int(0.2 * len(s_delta_avg))].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(roa_list)}, ignore_index=True)
    # 5. 最终筛选股票
    pb_list = get_fundamentals(query(
        valuation.code
    ).filter(
        valuation.code.in_(roa_list),
        valuation.pb_ratio > 0.7,
        valuation.ps_ratio < 3
    ).order_by(
        valuation.pb_ratio.asc()
    ))['code'].tolist()
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(pb_list)}, ignore_index=True)
    print(df_stocknum)
    final_list = pb_list[:g.stock_num]
    return final_list
```

  * **功能说明** : 通过多因子筛选过程，从最初的股票池中逐步筛选出符合条件的优质股票。

  * **关键逻辑** :

    * 筛选的四个步骤包括：低负债筛选、优质资产周转、ROA改善、最终筛选，确保选出的股票具备稳定的财务基础和增长潜力。

3\. 调仓函数 (adjust_position)

```python
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            order_target(stock, 0)  # 卖出不在新股票池中的股票
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash * g.position / (g.stock_num - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                order_target_value(stock, value)
                if len(context.portfolio.positions) == g.stock_num:
                    break
```

  * **功能说明** : 该函数用于执行调仓操作，卖出

不再符合条件的股票，并买入新的符合条件的股票，确保仓位合理分配。

  * **关键逻辑** :

    * 先卖后买，保证仓位调整过程中不超过预设的持仓数量。

总结

**低负债高周转多因子选股策略** 通过严谨的多因子选股方法，筛选出财务稳健且具有成长潜力的公司，并通过动态调仓机制保持投资组合的优质性。该策略适合注重基本面分析且希望长期获取稳定收益的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
