# 27、多因子动量轮动交易策略

### 策略简介

“多因子动量轮动交易策略”是一种结合多因子筛选和动量轮动的量化交易策略。该策略通过分析市场风格，动态调整大盘股和小盘股的持仓比例，并结合多因子筛选机制，筛选出具有良好基本面和成长性的股票进行投资。策略使用动量指标来判断市场风格，并根据特定的买入和卖出规则进行交易。

### 策略结构与功能

### 1. 初始化函数

```python
def initialize(context):
    set_benchmark('399317.XSHE')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 用真实价格交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    set_slippage(FixedSlippage(0.02))  # 设置滑点为0.02
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0005, close_commission=0.0005, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('system', 'error')  # 过滤低于error级别的日志
    g.index_pool = ['000016.XSHG', '399303.XSHE']  # 指数池
    g.momentum_day = 89  # 动量计算的时间窗口
    g.position = 1  # 仓位
    g.stock_num = 10  # 大盘股持仓数量
    g.stock_num_small = 30  # 小盘股持仓数量
    run_monthly(my_sell, monthday=-10, time='11:00', reference_security='399317.XSHE')  # 卖出操作
    run_monthly(my_buy, monthday=-1, time='11:15', reference_security='399317.XSHE')  # 买入操作
```

  * **功能说明** :

    * 初始化策略的各项设置，包括基准、真实价格、滑点、交易成本、指数池及动量轮动参数等。

    * 每月固定时间执行买入和卖出操作。

### 2. 动量计算与市场风格判断

```python
def get_index_signal(index_pool):
    score_list = []
    for index in index_pool:
        data = attribute_history(index, g.momentum_day, '1d', ['low'])
        y = np.log(data.low)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        annualized_returns = math.pow(math.exp(slope), 250) - 1
        r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
        score = annualized_returns * r_squared
        score_list.append(score)
    index_dict = dict(zip(index_pool, score_list))
    best_index = sorted(index_dict.items(), key=lambda item: item[1], reverse=True)[0][0]
    return best_index
```

  * **功能说明** :

    * 通过动量指标计算不同指数的强弱，并根据动量得分选出最强的指数，决定市场风格的切换（大盘风格或小盘风格）。

### 3. 股票筛选

**3.1 过滤股票列表**

```python
def filter_stock(context):
    curr_data = get_current_data()
    yesterday = context.previous_date
    by_date = yesterday - datetime.timedelta(days=1200)  # 过滤次新股（3年以内上市的股票）
    initial_list = get_all_securities(date=by_date).index.tolist()
    filtered_list = [stock for stock in initial_list if not (
        (curr_data[stock].day_open == curr_data[stock].high_limit) or
        (curr_data[stock].day_open == curr_data[stock].low_limit) or
        curr_data[stock].paused or
        'ST' in curr_data[stock].name or
        '*' in curr_data[stock].name or
        '退' in curr_data[stock].name or
        stock.startswith('688'))]
    return filtered_list
```

  * **功能说明** :

    * 过滤掉次新股、ST股、涨跌停股票、停牌股票和科创板股票等不符合条件的股票，获得初步筛选的股票列表。

**3.2 大盘价值成长风格股票筛选**

```python
def get_value_stock_list(context):
    print("大盘价值成长风格")
    df_stocknum = pd.DataFrame(columns=['过滤后的股票'])
    initial_list = filter_stock(context)
    # 1. 过滤流通市值大于市场中位数的股票
    df1 = get_fundamentals(query(valuation.circulating_cap, balance.total_current_assets, balance.total_current_liability, indicator.inc_return, income.np_parent_company_owners, valuation.code).filter(valuation.code.in_(initial_list)), date=context.previous_date)
    df1['current'] = df1['total_current_assets'] / df1['total_current_liability']
    current_median = df1['current'].median()
    roe_median = df1['inc_return'].median()
    np_parent_company_owners_median = np.median([one for one in df1['np_parent_company_owners'] if one >= 0])
    df1 = df1.sort_values('circulating_cap', ascending=False)
    list_1 = list(df1.code)[:int(0.5 * len(df1.code))]
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_1)}, ignore_index=True)
    # 2. 流动比率大于市场中位数的股票
    df2 = get_fundamentals(query(balance.total_current_assets, balance.total_current_liability, valuation.code).filter(valuation.code.in_(list_1)), date=context.previous_date)
    df2['current'] = df2['total_current_assets'] / df2['total_current_liability']
    list_2 = list(df2[df2['current'] > current_median].code)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_2)}, ignore_index=True)
    # 3. ROE大于市场中位数的股票
    df3 = get_fundamentals(query(indicator.inc_return, valuation.code).filter(valuation.code.in_(list_2)), date=context.previous_date)
    list_3 = list(df3[df3['inc_return'] > roe_median].code)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_3)}, ignore_index=True)
    # 4. 近四个季度自由现金流量均为正值
    df4 = get_history_fundamentals(list_3, fields=[indicator.code, cash_flow.net_operate_cash_flow, cash_flow.net_invest_cash_flow, cash_flow.fix_intan_other_asset_acqui_cash], watch_date=context.previous_date, count=4, interval='1q').dropna()
    df4['FCF'] = df4['net_operate_cash_flow'] - df4['fix_intan_other_asset_acqui_cash']
    s_delta_avg = df4.groupby('code')['FCF'].apply(lambda x: x.min() > 0).sort_values(ascending=False)
    list_4 = list(s_delta_avg[s_delta_avg > 0].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_4)}, ignore_index=True)
    # 5. 营业利润增长率大于10%的股票
    df5 = get_history_fundamentals(list_4, fields=[indicator.code, indicator.inc_operation_profit_year_on_year], watch_date=context.previous_date, count=4, interval='1q').dropna()
    s_delta_avg = df5.groupby('code')['inc_operation_profit_year_on_year'].apply(lambda x: x.min() > 10).sort_values(ascending=False)
    list_5 = list(s_delta_avg[s_delta_avg > 0].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_5)}, ignore_index=True)
    # 6. 归母净利润大于行业两倍中位数的股票
    df6 = get_history_fundamentals(list_5, fields=[indicator.code, income.np_parent_company_owners], watch_date=context.previous_date, count=4, interval='1q').dropna()
    s_delta_avg = df6.groupby('code')['np_parent_company_owners'].apply(lambda x: x.min() > 2 * np_parent_company_owners_median).sort_values(ascending=False)
    list_6 = list(s_delta_avg[s_delta_avg > 0].index)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_6)}, ignore_index=True)
    # 7. 按市净率选取低的股票
    df7 = get_fundamentals(query(valuation.pb_ratio, valuation.code).filter(valuation.code.in_(list_6)), date=context.previous_date)
 df7 = df7.sort_values('pb_ratio', ascending=True)
    list_7 = list(df7[:g.stock_num].code)
    df_stocknum = df_stocknum.append({'当前符合条件股票数量': len(list_7)}, ignore_index=True)
    print(df_stocknum)
    return list_7[:g.stock_num], len(list_6)
```

  * **功能说明** :

    * 对于市场处于大盘风格时，筛选流通市值较大、经营稳健、持续成长、估值合理的股票，构建大盘价值成长风格的股票池。

**3.3 小盘业绩炒作风格股票筛选**

```python
def get_growth_stock_list(context):
    print("小盘业绩炒作风格")
    initial_list = filter_stock(context)
    df = get_fundamentals(query(valuation.code).filter(
        valuation.code.in_(initial_list),
        valuation.pb_ratio > 0,
        indicator.inc_return > 0,
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0,
        indicator.ocf_to_operating_profit > 5,
    ).order_by(valuation.market_cap.asc()))
    choice = list(df.code)[:g.stock_num_small]
    return choice, len(choice)
```

  * **功能说明** :

    * 对于市场处于小盘风格时，筛选出成长性较好、市值较小的股票，构建小盘业绩炒作风格的股票池。

### 4. 股票交易与调仓

**4.1 卖出操作**

```python
def adjust_position_sell(context, buy_stocks):
    index_signal = get_index_signal(g.index_pool)
    for stock in context.portfolio.positions:
        current_data = get_current_data()
        now_price = current_data[stock].last_price
        # 根据不同条件进行卖出操作
        if index_signal == '000016.XSHG' and now_price < context.portfolio.positions[stock].avg_cost * 0.85:
            order_target(stock, 0)  # 大盘股跌幅超过15%止损
            log.info('大盘股跌幅超15%止损卖出: ' + str(stock))
        elif index_signal == '399303.XSHE' and now_price < context.portfolio.positions[stock].avg_cost * 0.95:
            order_target(stock, 0)  # 小盘股跌幅超过5%止损
            log.info('小盘股跌幅超5%止损卖出: ' + str(stock))
        elif stock not in buy_stocks:
            order_target(stock, 0)  # 不在买入列表中的股票卖出
            log.info('卖出不在买入列表中的股票: ' + str(stock))
```

  * **功能说明** :

    * 根据市场风格和个股表现执行不同的止损策略，并卖出不在买入列表中的股票。

**4.2 买入操作**

```python
def adjust_position_buy(context, buy_stocks):
    position_count = len(context.portfolio.positions)
    if g.stock_num >= position_count:
        for stock in buy_stocks:
            psize = context.portfolio.total_value * 2 / (g.stock_num + 4 + buy_stocks.index(stock))
            G = get_bars(stock, 1, '1d', ['high', 'low', 'open', 'close'], end_dt=context.current_dt, include_now=True)
            r = np.mean(list(G[0]))
            H = get_bars(stock, 50, '1d', ['high', 'low', 'open', 'close'], end_dt=context.current_dt, include_now=True)
            j = [np.mean(list(a)) for a in H]
            p = (r - np.mean(j)) / np.std(j)
            if context.portfolio.available_cash < psize:
                break
            if stock not in context.portfolio.positions:
                if p < -2:
                    log.info('短期超卖，多买点: ' + str(stock))
                    order_target_value(stock, 1.5 * psize)
                elif p > 2:
                    log.info('短期超买，少买点: ' + str(stock))
                    order_target_value(stock, 0.5 * psize)
                else:
                    order_value(stock, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break
```

  * **功能说明** :

    * 根据动量和市场风格买入股票，计算每只股票的买入金额，并根据短期超买超卖情况调整买入金额。



### 总结

多因子动量轮动交易策略通过市场风格切换、动量分析、基本面筛选等多种因子，筛选出合适的股票构建投资组合。策略在大盘和小盘之间进行灵活的切换，并根据不同的市场风格选择对应的投资组合，在实现投资收益最大化的同时，有效地控制了风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
