# 17、动态因子精选策略

### 策略说明

### 1. 初始化函数 (initialize)

**功能说明** : 设置策略的基准、交易选项、日志级别及手续费等。初始化时设置了股票持仓数量、监控涨停的时间范围等。

**代码** :

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来数据
    log.set_level('order', 'error')  # 过滤订单日志
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易手续费
    g.stock_num = 5  # 持股数
    g.limit_days = 20  # 检查最近20天内的涨停股票
    g.hold_list = []  # 已持股列表
    g.history_hold_list = []  # 历史持股列表
    g.not_buy_again_list = []  # 不再购买的股票列表
    g.switch = 0  # 开关
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 每天9:05运行
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一9:30运行
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 每天下午14:00运行
    run_daily(check_csy, time='09:30', reference_security='000300.XSHG')  # 每天早上9:30运行
```

### 2. 选股模块 (get_single_factor_list, sorted_by_circulating_market_cap, get_stock_list)

**功能说明** :

  * **get_single_factor_list** : 根据因子值对股票列表进行排序，选择指定比例的股票。

  * **sorted_by_circulating_market_cap** : 按照市值对股票列表进行排序，并取前几个。

  * **get_stock_list** : 综合多个因子（营业收入增长率、盈利增长率、PEG等），筛选并返回符合条件的股票列表。

**代码** :

```python
def get_single_factor_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    s_score = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].dropna().sort_values(ascending=sort)
    return s_score.index[int(p1 * len(stock_list)):int(p2 * len(stock_list))].tolist()
def sorted_by_circulating_market_cap(stock_list, n_limit_top=5):
    q = query(valuation.code).filter(valuation.code.in_(stock_list), indicator.eps > 0).order_by(valuation.circulating_market_cap.asc()).limit(n_limit_top)
    return get_fundamentals(q)['code'].tolist()
def get_stock_list(context):
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    initial_list = filter_kcb_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    sg_list = get_single_factor_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    sg_list = sorted_by_circulating_market_cap(sg_list)
    factor_list = ['operating_revenue_growth_rate', 'total_profit_growth_rate', 'net_profit_growth_rate', 'earnings_growth']
    factor_values = get_factor_values(initial_list, factor_list, end_date=context.previous_date, count=1)
    df = pd.DataFrame(index=initial_list)
    for factor in factor_list:
        df[factor] = factor_values[factor].iloc[0]
    df['total_score'] = 0.1 * df['operating_revenue_growth_rate'] + 0.15 * df['total_profit_growth_rate'] + 0.15 * df['net_profit_growth_rate'] + 0.6 * df['earnings_growth']
    ms_list = df.sort_values(by=['total_score'], ascending=False).index[:int(0.1 * len(df))].tolist()
    ms_list = sorted_by_circulating_market_cap(ms_list)
    peg_list = get_single_factor_list(context, initial_list, 'PEG', True, 0, 0.2)
    peg_list = get_single_factor_list(context, peg_list, 'turnover_volatility', True, 0, 0.5)
    peg_list = sorted_by_circulating_market_cap(peg_list)
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    union_list = sorted_by_circulating_market_cap(union_list, 12)
    print('选股结果：', union_list)
    return union_list
```

### 3. 准备股票池 (prepare_stock_list)

**功能说明** : 获取当前持股列表，更新历史持股列表和不再购买的股票列表，并检查涨停股票。

**代码** :

```python
def prepare_stock_list(context):
    g.hold_list = list(context.portfolio.positions)
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        temp_set = temp_set.union(set(hold_list))
    g.not_buy_again_list = list(temp_set)
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close==high_limit and paused==0')['code'].tolist()
```

### 4. 每周调整持仓 (weekly_adjustment)

**功能说明** : 获取并筛选目标股票列表，调整持仓，卖出不符合条件的股票，买入新的股票。

**代码** :

```python
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limit_stock(context, target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in target_list if stock not in black_list]
    if len(target_list) > 10:
        target_list = target_list[:10]
    h_ma = history(20 + 20, '1d', 'close', target_list).rolling(window=20).mean().iloc[20:]
    X = np.arange(len(h_ma))
    tmp_target_list = []
    for stock in target_list:
        MA_N_Arr = h_ma[stock].values
        MA_N_Arr = MA_N_Arr - MA_N_Arr[0]
        slope = round(sm.OLS(MA_N_Arr, X).fit().params[0] * 100, 1)
        remove_it = False
        if slope < -2:
            if stock not in g.hold_list:
                print('{}下降趋势明显，切勿开仓'.format(stock))
                remove_it = True
        if not remove_it:
            tmp_target_list.append(stock)
    target_list = tmp_target_list
    gupiao = [get_security_info(s).display_name for s in target_list]
    print("提示买的股票列表%s" % gupiao)
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % stock)
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持有[%s]" % stock)
    position_count = len(context.portfolio.positions)
    target_num = g.stock_num
    if target_num > position_count:
        value = context.portfolio.available_cash / (target_num - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) >= g.stock_num:
                        break
```

### 5. 调整昨日涨停股票 (check_limit_up)

**功能说明** : 检查昨日涨停的股票是否依然涨停，若未涨停，则卖出。

**代码** :

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
                log.info("[%s]涨
停继续" % stock)
```

### 6. 检查股票标志 (check_csy)

**功能说明** : 检查股票是否为ST股票，若是，则卖出。

**代码** :

```python
def check_csy(context):
    target_list = list(context.portfolio.positions)
    st_list = get_st_stock()
    for stock in target_list:
        if stock in st_list:
            log.info("[%s]为ST股，卖出" % stock)
            position = context.portfolio.positions[stock]
            close_position(position)
```

### 总结

动态因子精选策略是一种综合多种因子的选股方法，通过严格的筛选和定期调整来优化股票投资组合。此策略结合了因子分析、历史表现、以及股票的涨停情况，致力于在市场中筛选出最具潜力的股票，并实时调整持仓，以实现长期稳健的投资收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
