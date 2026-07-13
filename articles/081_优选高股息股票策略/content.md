# 81、优选高股息股票策略

# 策略概述

**优选高股息股票策略** 是一种基于高股息率选股的量化投资策略。该策略通过筛选近一年内股息率较高的股票，并结合市净率和回报率等财务指标，剔除风险较高的个股，如ST股、停牌股等。策略每月定期调仓，旨在通过持有高股息的股票组合来实现稳健的投资回报。

### 各部分功能代码与详细说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    # 设定基准
    set_benchmark('510880.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    log.set_level('system', 'error')
    # 设置股票数量
    g.stocknum = 30
    # 每月调仓
    run_monthly(trade, 1, '10:00')
```

  * **功能说明** : 初始化策略时，设定交易基准、开启真实价格模式、避免未来数据使用，并设置了每月调仓的时间。

  * **关键参数** :

    * g.stocknum: 目标持仓股票数量，每月根据筛选结果动态调整。

2\. 交易函数 (trade)

```python
def trade(context):
    end_date = context.previous_date
    current_data = get_current_data()
    # 获取所有股票代码
    stocks = get_all_securities('stock', end_date).index.tolist()
    # 基本财务指标筛选
    q = query(
        valuation.code
    ).filter(
        valuation.code.in_(stocks),
        valuation.pb_ratio > 0,
        indicator.inc_return > 0
    )
    stocks = list(get_fundamentals(q).code)
    # 根据股息率筛选
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.1)[:100]
    # 进一步过滤风险股
    stocks = [
        stock for stock in stocks if not (
            current_data[stock].paused or
            current_data[stock].is_st or
            ('ST' in current_data[stock].name) or
            ('*' in current_data[stock].name) or
            ('退' in current_data[stock].name) or
            (current_data[stock].last_price == current_data[stock].high_limit) or
            (current_data[stock].last_price == current_data[stock].low_limit)
        )
    ]
    # 限制最终股票数量
    stocks = stocks[:g.stocknum]
    # 调整持仓
    for s in context.portfolio.positions:
        if s not in stocks:
            order_target(s, 0)
    psize = context.portfolio.total_value / g.stocknum
    for s in stocks:
        if len(context.portfolio.positions) >= g.stocknum:
            break
        if s not in context.portfolio.positions:
            order_value(s, psize)
    record(stocknum=len(context.portfolio.positions))
```

  * **功能说明** : 策略每月对股票池进行筛选并调仓。首先，基于基本的财务指标进行初步筛选，然后根据股息率进一步筛选出高股息股票，最后剔除停牌股、ST股及涨跌停股，最终确定持仓股票。

  * **关键逻辑** :

    * 筛选市净率为正且回报率为正的股票。

    * 根据股息率进行排序，并选取前10%的股票进行投资。

3\. 股息率筛选函数 (get_dividend_ratio_filter_list)

```python
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365*3)
    # 获取分红数据
    interval = 1000
    list_len = len(stock_list)
    q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
    ).filter(
        finance.STK_XR_XD.a_registration_date >= time0,
        finance.STK_XR_XD.a_registration_date <= time1,
        finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)])
    )
    df = finance.run_query(q)
    # 处理数据
    if list_len > interval:
        df_num = list_len // interval
        for i in range(df_num):
            q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
            ).filter(
                finance.STK_XR_XD.a_registration_date >= time0,
                finance.STK_XR_XD.a_registration_date <= time1,
                finance.STK_XR_XD.code.in_(stock_list[interval*(i+1):min(list_len, interval*(i+2))])
            )
            temp_df = finance.run_query(q)
            df = df.append(temp_df)
    # 计算股息率
    dividend = df.fillna(0).set_index('code').groupby('code').sum()
    temp_list = list(dividend.index)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(temp_list))
    cap = get_fundamentals(q, date=time1)
    cap = cap.set_index('code')
    DR = pd.concat([dividend, cap], axis=1, sort=False)
    DR['dividend_ratio'] = (DR['bonus_amount_rmb']/10000) / DR['market_cap']
    # 排序并筛选
    DR = DR.sort_values(by=['dividend_ratio'], ascending=sort)
    final_list = list(DR.index)[int(p1*len(DR)):int(p2*len(DR))]
    return final_list
```

  * **功能说明** : 计算并筛选股息率较高的股票，返回满足条件的股票列表。

  * **关键逻辑** :

    * 查询过去三年内的分红数据，计算每只股票的年化股息率。

    * 按照股息率从高到低排序，并根据指定比例筛选出股票。

### 总结

**优选高股息股票策略** 通过筛选高股息股票，并结合财务指标和风险控制条件，定期进行持仓调整。该策略能够在保证一定收益率的同时，控制投资风险，适合追求稳健收益的长期投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
