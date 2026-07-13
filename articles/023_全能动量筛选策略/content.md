# 23、全能动量筛选策略

### 1. 简介

“全能动量筛选策略”是一种基于多因子选股和动量交易的量化投资策略。该策略综合利用多个因子进行选股，通过过滤掉不符合条件的股票，再依据动量模型进行买卖决策。策略的核心是优化选股池，并动态调整持仓组合，以实现持续优化的回报率。

### 2. 策略初始化

```python
def initialize(context):
    # 设定基准
    set_benchmark('000300.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三，不同滑点影响可在归因分析中查看
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5),type='stock')
    # 过滤order中低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10
    g.hold_list = [] # 当前持仓的全部股票
    g.target_list = []
    g.yesterday_HL_list = [] # 记录持仓中昨日涨停的股票
    g.not_buy_again = []
    g.factor_list = [
        'price_no_fq', # 技术指标因子 不复权价格因子
        'total_profit_to_cost_ratio', # 质量类因子 成本费用利润率
        'inventory_turnover_rate' # 质量类因子 存货周转率
    ]
    # 设置交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, 1, time='9:30', reference_security='000300.XSHG')
    run_daily(trade_morning,time='9:26',reference_security='000300.XSHG')
    run_daily(trade_afternoon, time='13:00', reference_security='000300.XSHG')
```

  * **功能说明** : 初始化策略参数，设置交易环境（基准、滑点、成本等），并定义全局变量以管理持仓、目标股票列表等信息。此策略每周进行一次主要的持仓调整，并在特定时段执行买卖操作。

### 3. 股票池准备与选股

**3.1 股票池准备**

```python
def prepare_stock_list(context):
    g.hold_list= []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    if g.hold_list != []:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.yesterday_HL_list = list(df.code)
    else:
        g.yesterday_HL_list = []
    g.target_list = get_stock_list(context)
```

  * **功能说明** : 准备当日股票池，包括当前持仓列表、昨日涨停股票列表、以及根据因子模型筛选后的目标股票列表。

**3.2 选股模块**

```python
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    factor_values = get_factor_values(initial_list, [
        g.factor_list[0],
        g.factor_list[1],
        g.factor_list[2],
        ], end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
    df[g.factor_list[0]] = list(factor_values[g.factor_list[0]].T.iloc[:,0])
    df[g.factor_list[1]] = list(factor_values[g.factor_list[1]].T.iloc[:,0])
    df[g.factor_list[2]] = list(factor_values[g.factor_list[2]].T.iloc[:,0])
    df = df.dropna()
    coef_list = [
        -6.123355346008858e-05,
        -0.002579342458393642,
        -2.194257357346814e-06
        ]
    df['total_score'] = coef_list[0]*df[g.factor_list[0]] + coef_list[1]*df[g.factor_list[1]] + coef_list[2]*df[g.factor_list[2]]
    df = df.sort_values(by=['total_score'], ascending=False)
    complex_factor_list = list(df.index)[:max(int(0.1*len(list(df.index))),g.stock_num)]
    q = query(valuation.code,valuation.circulating_market_cap,indicator.eps).filter(valuation.code.in_(complex_factor_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    df = df[df['eps']>0]
    final_list  = list(df.code)
    final_list = filter_paused_stock(final_list)
    final_list = filter_limitup_stock(context, final_list)
    final_list = filter_limitdown_stock(context, final_list)
    return final_list
```

  * **功能说明** : 通过技术指标与基本面因子筛选出符合条件的股票。计算每个股票的综合评分，并根据评分从高到低选择一定比例的股票，过滤掉暂停交易、涨停和跌停的股票后，返回最终的目标股票列表。

### 4. 交易与调仓

**4.1 持仓调整**

```python
def weekly_adjustment(context):
    g.not_buy_again = []
    target_list = g.target_list
    target_list = target_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.yesterday_HL_list):
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("持有[%s]" % (stock))
    buy_security(context,target_list)
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.not_buy_again.append(stock)
```

  * **功能说明** : 每周对持仓进行调整。卖出不再符合条件的股票，并买入目标列表中的新股票。已买入的股票将被记录以避免重复购买。

**4.2 涨停检查与尾盘交易**

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.yesterday_HL_list != []:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close','high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0,0] < current_data.iloc[0,1]:
                log.info("[%s]涨停打开，卖出" % (stock))
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % (stock))
```

  * **功能说明** : 每天下午检查持仓中昨日涨停的股票，若当天涨停打开，则卖出该股票。

**4.3 剩余资金买入**

```python
def check_remain_amount(context):
    g.hold_list= []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    if len(g.hold_list) < g.stock_num:
        target_list = g.target_list
        target_list = filter_not_buy_again(target_list)
        target_list = target_list[:min(g.stock_num, len(target_list))]
        buy_security(context,target_list)
```

  * **功能说明** : 检查是否有剩余资金，并买入新的目标股票，确保资金有效利用。

### 5. 辅助函数

  * **过滤器** :

    * **filter_paused_stock** : 过滤停牌股票

    * **filter_st_stock** : 过滤ST及退市风险股票

    * **filter_kcbj_stock** : 过滤科创板和北交所股票

    * **filter_limitup_stock** : 过滤涨停股票

    * **filter_limitdown_stock** : 过滤跌停股票

    * **filter_new_stock** : 过滤次新股

    * **filter_not_buy_again** : 过滤本周一已买入的股票

  * **交易模块** :

    * **ordertarget_value** : 自定义下单函数

    * **open_position** : 开仓函数

    * **close_position** : 平仓函数

    * **buy_security** : 执行买入操作

### 6. 数据记录与通知

  * **print_position_info** : 打印每日持仓信息

  * **send_email** : 发送交易通知邮件



### 7. 总结

“全能动量筛选策略”通过多因子选股和动态调整持仓的方式，旨在最大化策略收益并控制风险。该策略充分利用了技术指标与基本面数据，结合严谨的过滤条件，提供了一个高效的投资管理工具。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
