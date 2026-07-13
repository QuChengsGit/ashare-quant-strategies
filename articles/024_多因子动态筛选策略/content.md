# 24、多因子动态筛选策略

### 简介

“多因子动态筛选策略”是一种基于多因子模型的量化投资策略。该策略通过多个因子筛选出符合条件的股票，并结合账户资金再平衡机制，动态调整持仓，确保持仓组合的优质性与风险控制。策略通过技术指标、情绪因子、动量因子、风格因子、以及质量因子的综合分析，对股票进行评分，最终选择出评分最高的一批股票进行投资。

### 策略初始化

```python
def initialize(context):
    # 设定基准
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 过滤order中低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.no_trading_today_signal = False
    g.stock_num = 1
    g.hold_list = []  # 当前持仓的全部股票
    g.yesterday_HL_list = []  # 记录持仓中昨日涨停的股票
    # 定义因子与对应的系数
    g.factor_list = [
        # 因子组合1
        ([
            'ARBR', # 情绪类因子
            'SGAI', # 销售管理费用指数
            'net_profit_to_total_operate_revenue_ttm', # 净利润与营业总收入之比
            'retained_profit_per_share' # 每股未分配利润
        ], [
            -0.00015399364219672028,
            0.0068040696770965275,
            -0.013582394749579795,
            -0.05043296392026463
        ]),
        # 因子组合2
        ([
            'Price1Y', # 动量类因子
            'total_profit_to_cost_ratio', # 成本费用利润率
            'VOL120' # 120日平均换手率
        ], [
            -1.6481969388084845,
            -0.17062057099935446,
            -0.061842557079243125
        ]),
        # 因子组合3
        ([
            'debt_to_assets', # 资产负债率
            'operating_cost_to_operating_revenue_ratio', # 销售成本率
            'DAVOL20', # 20日平均换手率与120日平均换手率之比
            'price_no_fq', # 不复权价格因子
            'sales_growth' # 5年营业收入增长率
        ], [
            0.058175841938529524,
            -0.1910332189773409,
            -0.2736912625714264,
            -0.027468330345688075,
            0.11887746662741136
        ])
    ]
    # 设置交易运行时间
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00') #检查持仓中的涨停股是否需要卖出
    run_daily(close_account, '14:30')
    run_daily(print_position_info, '15:10')
```

  * **功能说明** : 初始化策略参数，设置交易环境（基准、滑点、成本等），并定义全局变量以管理持仓、目标股票列表等信息。通过不同因子组合对股票进行筛选和评分。

### 股票池准备与选股

**1.1 准备股票池**

```python
def prepare_stock_list(context):
    g.hold_list = [position.security for position in list(context.portfolio.positions.values())]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.yesterday_HL_list = list(df.code)
    else:
        g.yesterday_HL_list = []
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')
```

  * **功能说明** : 准备当日股票池，包括当前持仓列表、昨日涨停股票列表，并判断当天是否为账户资金再平衡的日期。

**1.2 选股模块**

```python
def get_stock_list(context):
    yesterday = context.previous_date
    today = context.current_dt
    initial_list = get_all_securities('stock', today).index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    final_list = []
    for factor_list, coef_list in g.factor_list:
        factor_values = get_factor_values(initial_list, factor_list, end_date=yesterday, count=1)
        df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
        for i in range(len(factor_list)):
            df[factor_list[i]] = list(factor_values[factor_list[i]].T.iloc[:, 0])
        df = df.dropna()
        df['total_score'] = sum(coef_list[i] * df[factor_list[i]] for i in range(len(factor_list)))
        df = df[df['total_score'] > 0].sort_values(by='total_score', ascending=False)
        complex_factor_list = list(df.index)[:int(0.1 * len(df))]
        q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(complex_factor_list)).order_by(valuation.circulating_market_cap.asc())
        df = get_fundamentals(q)
        df = df[df['eps'] > 0]
        lst = filter_paused_stock(list(df.code))
        lst = filter_limitup_stock(context, lst)
        lst = filter_limitdown_stock(context, lst)
        lst = lst[:min(g.stock_num, len(lst))]
        final_list.extend([stock for stock in lst if stock not in final_list])
    return final_list
```

  * **功能说明** : 通过多个因子组合筛选出符合条件的股票，并根据评分筛选出最优的股票列表，过滤掉暂停交易、涨停和跌停的股票后，返回最终的目标股票列表。

### 交易与调仓

**1.3 整体调整持仓**

```python
def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        for stock in g.hold_list:
            if (stock not in target_list) and (stock not in g.yesterday_HL_list):
                log.info("卖出[%s]" % (stock))
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("已持有[%s]" % (stock))
        position_count = len(context.portfolio.positions)
        target_num = len(target_list)
        if target_num > position_count:
            value = context.portfolio.cash / (target_num - position_count)
            for stock in target_list:
                if context.portfolio.positions[stock].total_amount == 0:
                    if open_position(stock, value):
                        if len(context.portfolio.positions) == target_num:
                            break
```

  * **功能说明** : 每周对持仓进行调整，卖出不符合条件的股票，并买入目标列表中的新股票。

**1.4 调整昨日涨停股票**

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close','high_limit'], count=1, panel=False)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                log.info("[%s]涨停打开，卖出" % (stock))
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % (stock))
```

  * **功能说明** : 检查昨日涨停的股票，若当天涨停打开，则卖出该股票。

辅助函数

  * **过滤器** :

    * **filter_paused_stock** : 过滤停牌股票

    * **filter_st_stock** : 过滤ST及退市风险股票

    * **filter_kcbj_stock** : 过滤科创板和北交所股票

    * **filter_limitup_stock** : 过滤涨

停股票

  * **filter_limitdown_stock** : 过滤跌停股票

  * **filter_new_stock** : 过滤次新股

  * **交易模块** :

    * **ordertarget_value** : 自定义下单逻辑

    * **open_position** : 开仓逻辑

    * **close_position** : 平仓逻辑

  * **资金管理** :

    * **today_is_between** : 判断当天是否为账户再平衡日期

    * **close_account** : 在资金再平衡期结束时，清空持仓

  * **信息打印** :

    * **print_position_info** : 打印每日持仓和交易信息



### 策略总结

“多因子动态筛选策略”通过对多种因子的综合分析和筛选，灵活调整持仓组合，旨在捕捉市场中的优质机会并规避风险。策略充分利用了动量、情绪、质量、技术指标等多种因子，构建出科学有效的投资组合，在实现收益最大化的同时严格控制风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
