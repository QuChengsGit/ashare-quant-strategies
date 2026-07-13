# 95、多因子高股息择时策略

# 策略概述

**多因子高股息择时策略** 是一种结合多因子选股和动态仓位管理的量化交易策略，专注于筛选股息率较高的股票，通过波动率、财务杠杆等多因子筛选，并结合市场热点（如涨停板）进行调整。策略的核心目标是在市场中筛选出具有稳定收益潜力的股票，尤其是那些股息率高、财务健康、波动率适中的标的，并通过周期性调仓和实时监控动态调整持仓，以获得持续稳健的收益。

# 策略详细介绍

  1. **策略思想** ：

     * **多因子选股** ：结合股息率、波动率和财务杠杆等因子，从市场中筛选出财务稳健且具备一定增长潜力的股票。

     * **市场热点监控** ：关注市场热点，如涨停板等动态指标，及时调整持仓，捕捉短期市场机会。

     * **动态调仓** ：通过定期和实时的调仓机制，确保投资组合中持有的股票始终处于优质标的之列。

     * **风险控制** ：通过对股票涨跌停、ST股、次新股等的筛选，降低市场风险。

  2. **关键要素** ：

     * **股息率筛选** ：通过对股票的股息率进行计算和筛选，确保所选股票具有较高的股息收益。

     * **因子筛选** ：结合波动率和财务杠杆等因子进行筛选，进一步优化股票池。

     * **仓位管理** ：结合动态调仓和风控机制，灵活管理仓位，适应不同市场环境。

# 策略代码与功能说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='fund')
    log.set_level('order', 'error')
    g.stock_num = 10  # 最大持仓数
    g.limit_days = 20  # 保持一定周期内的持仓记录
    g.limit_up_list = []  # 涨停股票列表
    g.hold_list = []  # 当前持仓股票
    g.history_hold_list = []  # 历史持仓记录
    g.not_buy_again_list = []  # 不再买入的股票列表
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

  * **功能说明** : 初始化策略，设定交易基准、滑点、交易成本等基础参数，并定义每日和每周需要运行的调度任务。

  * **关键逻辑** :

    * 设置交易参数（如交易基准、滑点、成本等）以确保交易环境的真实与合理性。

    * 初始化全局变量，以便后续操作中维护策略状态。

2\. 股息率筛选 (get_dividend_ratio_filter_list)

```python
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365)
    interval = 1000
    list_len = len(stock_list)
    q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
    ).filter(
        finance.STK_XR_XD.a_registration_date >= time0,
        finance.STK_XR_XD.a_registration_date <= time1,
        finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)]))
    df = finance.run_query(q)
    if list_len > interval:
        df_num = list_len // interval
        for i in range(df_num):
            q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
            ).filter(
                finance.STK_XR_XD.a_registration_date >= time0,
                finance.STK_XR_XD.a_registration_date <= time1,
                finance.STK_XR_XD.code.in_(stock_list[interval*(i+1):min(list_len,interval*(i+2))]))
            temp_df = finance.run_query(q)
            df = df.append(temp_df)
    dividend = df.fillna(0).set_index('code').groupby('code').sum()
    temp_list = list(dividend.index)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(temp_list))
    cap = get_fundamentals(q, date=time1).set_index('code')
    DR = pd.concat([dividend, cap], axis=1, sort=False)
    DR['dividend_ratio'] = (DR['bonus_amount_rmb']/10000) / DR['market_cap']
    DR = DR.sort_values(by=['dividend_ratio'], ascending=sort)
    final_list = list(DR.index)[int(p1*len(DR)):int(p2*len(DR))]
    return final_list
```

  * **功能说明** : 根据过去一年的分红情况和当前市值，计算股票的股息率并进行排序筛选。

  * **关键逻辑** :

    * 通过筛选高股息率的股票，将优质高股息股纳入股票池，确保投资组合的稳定性和收益性。

3\. 选股模块 (get_stock_list)

```python
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_new_stock(context, initial_list, 375)
    initial_list = filter_st_stock(initial_list)
    dr_list = get_dividend_ratio_filter_list(context, initial_list, False, 0, 0.5)
    tv_list = get_factor_filter_list(context, dr_list, 'turnover_volatility', False, 0, 0.8)
    lev_list = get_factor_filter_list(context, tv_list, 'MLEV', True, 0, 0.5)
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(lev_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    final_list = list(df.code)[:15]
    return final_list
```

  * **功能说明** : 筛选股票池，通过股息率、波动率、财务杠杆等因子逐层筛选出优质股票，最终生成备选股票列表。

  * **关键逻辑** :

    * 通过多因子筛选，确保所选股票在多个方面具备优势，如股息收益、稳定性和财务健康。

4\. 准备股票池 (prepare_stock_list)

```python
def prepare_stock_list(context):
    g.hold_list = [position.security for position in list(context.portfolio.positions.values())]
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        for stock in hold_list:
            temp_set.add(stock)
    g.not_buy_again_list = list(temp_set)
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.high_limit_list = list(df.code)
    else:
        g.high_limit_list = []
```

  * **功能说明** : 准备每日的股票池，包括维护持仓记录、历史持仓列表以及不再买入的股票列表，并监控前一日涨停的股票。

  * **关键逻辑** :

    * 通过维护历史持仓记录，避免频繁买入同一股票，并通过监控涨停股票，及时捕捉市场热点。

5\. 调整持仓 (weekly_adjustment)

```python
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    target_list = target
_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
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

  * **功能说明** : 每周调整持仓，根据最新的股票筛选结果更新持仓，并及时卖出不再符合条件的股票。

  * **关键逻辑** :

    * 确保持仓的动态更新，使投资组合中的股票始终保持在高质量的备选池中。

6\. 处理涨停股票 (check_limit_up)

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close','high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0,0] < current_data.iloc[0,1]:
                log.info("[%s]涨停打开，卖出" % (stock))
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % (stock))
```

  * **功能说明** : 实时监控涨停股票，在尾盘时如果涨停板被打开则提前卖出，以避免次日可能的回调。

  * **关键逻辑** :

    * 动态管理涨停股票，确保及时锁定收益，防止因为涨停板打开后次日大幅回调造成损失。

7\. 辅助函数与工具

  * **过滤函数** ：如 filter_paused_stock、filter_st_stock、filter_limitup_stock 等，用于过滤不符合交易条件的股票。

  * **交易模块** ：包括 order_target_value_、open_position、close_position 等自定义下单和调仓函数，确保交易的合理性与高效性。

8\. 打印持仓信息 (print_position_info)

```python
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：'+str(_trade))
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print('代码:{}'.format(securities))
        print('成本价:{}'.format(format(cost,'.2f')))
        print('现价:{}'.format(price))
        print('收益率:{}%'.format(format(ret,'.2f')))
        print('持仓(股):{}'.format(amount))
        print('市值:{}'.format(format(value,'.2f')))
```

  * **功能说明** : 每日收盘后打印当日持仓情况和交易记录，便于策略运行监控。

  * **关键逻辑** :

    * 提供详细的持仓与交易信息，帮助投资者了解当前账户的资金动向与收益情况。

# 总结

**多因子高股息择时策略** 通过严谨的多因子筛选、动态调仓与严格的风险控制，实现了在不同市场环境下的稳定收益。策略结合了高股息选股、市场热点捕捉与实时监控机制，适用于希望在波动市场中获取稳定回报的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
