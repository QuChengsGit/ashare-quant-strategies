# 83、多因子选择与动态趋势调整策略

# 策略概述

**多因子选择与动态趋势调整策略** 是一种结合了多因子选股和动态趋势分析的量化投资策略。通过多因子分析筛选出具有高成长性、低估值及低波动性的股票，并结合趋势判断来调整持仓，以获取更优的收益风险比。策略通过每周的调仓机制和动态止盈策略来控制风险，力求在保证收益的同时减少回撤。

### 各部分功能代码与详细说明

1\. 初始化与全局变量设置 (initialize)

```python
def initialize(context):
    # 设定基准指数为中证500
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 防止未来数据的使用
    log.set_level('order', 'error')  # 仅记录error级别的日志
    # 初始化全局变量
    g.stock_num = 10  # 持仓股票数
    g.limit_days = 20  # 涨停后避免重新买入的天数
    g.hold_list = []  # 当前持仓列表
    g.history_hold_list = []  # 历史持仓记录
    g.not_buy_again_list = []  # 涨停后避免买入的股票列表
    # 设定每日、每周的运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
```

  * **功能说明** : 设置策略的初始化参数与全局变量，并设定每日与每周的调仓时间。

  * **关键逻辑** :

    * set_benchmark: 设置基准指数为中证500。

    * run_daily和run_weekly: 设定每日与每周运行的策略函数。

2\. 单因子筛选函数 (get_single_factor_list)

```python
def get_single_factor_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    s_score = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1
                                )[jqfactor].iloc[0].dropna().sort_values(ascending=sort)
    return s_score.index[int(p1 * len(stock_list)):int(p2 * len(stock_list))].tolist()
```

  * **功能说明** : 根据指定因子对股票列表进行筛选，返回指定百分位范围内的股票。

  * **关键逻辑** :

    * jqfactor: 选择的因子名称，如营业收入增长率、PEG等。

    * sort: 决定因子排序方向（升序或降序）。

    * p1和p2: 确定返回股票在排序中的百分比区间。

3\. 按流通市值排序并筛选 (sorted_by_circulating_market_cap)

```python
def sorted_by_circulating_market_cap(stock_list, n_limit_top=5):
    q = query(
        valuation.code,
    ).filter(
        valuation.code.in_(stock_list),
        indicator.eps > 0  # 筛选每股收益大于0的股票
    ).order_by(
        valuation.circulating_market_cap.asc()  # 按流通市值升序排序
    ).limit(
        n_limit_top
    )
    return get_fundamentals(q)['code'].tolist()
```

  * **功能说明** : 对股票按照流通市值进行升序排序，返回市值最小的前n_limit_top只股票。

  * **关键逻辑** :

    * 筛选市值小的股票，通常这些股票具有更大的增长潜力。

4\. 股票筛选主逻辑 (get_stock_list)

```python
def get_stock_list(context):
    # 去掉次新股
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 去除科创板及ST股票
    initial_list = filter_kcb_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 1. 筛选营业收入增长率最高的股票，并按流通市值筛选
    sg_list = get_single_factor_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    sg_list = sorted_by_circulating_market_cap(sg_list)
    # 2. 综合多个增长率因子，计算总评分并筛选
    factor_list = [
        'operating_revenue_growth_rate',  # 营业收入增长率
        'total_profit_growth_rate',  # 利润总额增长率
        'net_profit_growth_rate',  # 净利润增长率
        'earnings_growth',  # 5年盈利增长率
    ]
    factor_values = get_factor_values(initial_list, factor_list, end_date=context.previous_date, count=1)
    df = pd.DataFrame(index=initial_list)
    for factor in factor_list:
        df[factor] = factor_values[factor].iloc[0]
    df['total_score'] = 0.1 * df['operating_revenue_growth_rate'] + 0.35 * df['total_profit_growth_rate'] + 0.15 * df[
        'net_profit_growth_rate'] + 0.4 * df['earnings_growth']
    ms_list = df.sort_values(by=['total_score'], ascending=False).index[:int(0.1 * len(df))].tolist()
    ms_list = sorted_by_circulating_market_cap(ms_list)
    # 3. 筛选PEG最低的股票，并按流通市值筛选
    peg_list = get_single_factor_list(context, initial_list, 'PEG', True, 0, 0.2)
    peg_list = get_single_factor_list(context, peg_list, 'turnover_volatility', True, 0, 0.5)
    peg_list = sorted_by_circulating_market_cap(peg_list)
    # 将以上三组股票合并，并按流通市值排序
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    union_list = sorted_by_circulating_market_cap(union_list, 100)
    print('选股结果：', union_list)
    return union_list
```

  * **功能说明** : 综合多因子筛选策略，通过营收增长率、PEG等指标筛选出高潜力的股票。

  * **关键逻辑** :

    * 综合多个因子，分别从成长性、估值、波动性等角度对股票进行筛选，得到最终的目标股票列表。

5\. 股票池准备 (prepare_stock_list)

```python
def prepare_stock_list(context):
    # 获取已持有列表
    g.hold_list = list(context.portfolio.positions)
    # 获取最近一段时间持有过的股票列表
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        temp_set = temp_set.union(set(hold_list))
    g.not_buy_again_list = list(temp_set)
    # 获取持仓的昨日涨停列表
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'],
                       count=1, panel=False)
        g.high_limit_list = df.query('close==high_limit and paused==0')['code'].tolist()
```

  * **功能说明** : 准备每日的股票池，追踪历史持仓及涨停股票，避免重复买入。

  * **关键逻辑** :

    * 通过记录历史持仓和涨停股票，优化股票筛选过程，减少不必要的重复买入。

6\. 每周调仓逻辑 (weekly_adjustment)

```python
def weekly_adjustment(context):
    # 获取应买入列表
    target_list = get_stock_list(context)
    #
    target_list = filter_paused_stock(target_list)
    target_list = filter_limit_stock(context, target_list)
    # 排除黑名单股票（最近有涨停的股票）
    recent_limit_up_list = get_recent_limit_up_stock(context, target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in target_list if stock not in black_list]
    if len(target_list) > 10:
        target_list = target_list[:10]
    # 通过趋势斜率筛选目标股票
    h_ma = history(20 + 20, '1d', 'close', target_list).rolling(window=20).mean().iloc[20:]
    X = np.arange(len(h
_ma))
    tmp_target_list = []
    for stock in target_list:
        MA_N_Arr = h_ma[stock].values
        MA_N_Arr = MA_N_Arr - MA_N_Arr[0]  # 截距归零
        slope = round(sm.OLS(MA_N_Arr, X).fit().params[0] * 100, 1)
        remove_it = False
        if slope < -2:
            if stock not in g.hold_list:
                print('{}下降趋势明显，切勿开仓'.format(stock))
                remove_it = True
        if not remove_it:
            tmp_target_list.append(stock)
    #
    target_list = tmp_target_list
    # 调仓逻辑
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % stock)
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持有[%s]" % stock)
    position_count = len(context.portfolio.positions)
    target_num = min(len(set(target_list).union(set(context.portfolio.positions))), g.stock_num)
    if target_num > position_count:
        value = (target_num / g.stock_num) * context.portfolio.available_cash / (target_num - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) >= g.stock_num:
                        break
```

  * **功能说明** : 每周调整持仓，通过趋势分析和多因子筛选，剔除下行趋势明显的股票。

  * **关键逻辑** :

    * sm.OLS: 使用线性回归分析股票的趋势斜率，并根据斜率调整持仓。

    * 将符合条件的股票加入持仓列表，并卖出不再符合条件的股票。

7\. 昨日涨停股票调整 (check_limit_up)

```python
def check_limit_up(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info("[%s]涨停打开，卖出" % stock)
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % stock)
```

  * **功能说明** : 对昨日涨停的股票进行调整，如果涨停被打开则卖出。

  * **关键逻辑** :

    * 通过实时数据监控涨停状态，如果涨停打开则即时调整持仓。

### 总结

**多因子选择与动态趋势调整策略** 通过结合多因子选股模型和动态趋势分析，以获取更稳定的投资收益。策略注重成长性、估值与波动性等多个因素，并通过定期的调仓和趋势判断，确保持仓股票符合预期。该策略适合长期稳健投资者，同时具备较好的风险控制能力。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
