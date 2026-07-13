# 93、多因子动态情绪轮动策略

# 策略概述

**多因子动态情绪轮动策略** 是一种基于情绪周期、市场连板数和市值等多因子的量化策略。该策略通过监测市场情绪的变化，并结合特定股票的连板数、市值等因素，动态调整股票池和仓位分配。策略使用了双子账户机制，在不同的情绪周期中轮动持仓，以期在不同行情下获取稳健的收益。

# 策略详细介绍

  1. **策略思想** ：

     * **市场情绪监控** ：通过分析市场中股票的连板数，判断当前市场情绪的强弱，并以此指导后续的买卖决策。

     * **多因子选股** ：策略在选股时不仅考虑市场情绪，还结合股票的市值、上市时间、连板情况等多个因素，筛选出符合条件的股票进行交易。

     * **子账户轮动** ：策略使用两个子账户，分别在不同的情绪周期内进行轮动操作，以平衡风险和收益。

  2. **关键要素** ：

     * **情绪周期** ：策略通过计算过去一段时间内的连板数变化来判断市场的情绪周期，从而决定是否执行交易。

     * **多因子筛选** ：在市场情绪判断的基础上，进一步筛选出市值合理、上市时间较长、并且近期表现强势的股票。

     * **仓位管理** ：在每个情绪周期内，根据账户资金情况和子账户轮动机制，动态调整仓位，确保资金的合理使用和风险的有效控制。

# 策略代码与功能说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    set_benchmark('000300.XSHG')  # 设定沪深300为基准
    set_option('use_real_price', True)  # 开启真实价格模式
    set_option("avoid_future_data", True)  # 避免未来数据
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易成本
    init_cash = context.portfolio.starting_cash / 2
    set_subportfolios([
        SubPortfolioConfig(cash=init_cash, type='stock'),
        SubPortfolioConfig(cash=init_cash, type='stock'),
    ])
    g.buy_stock = 0  # 初始化每日操作股票
    g.count_days = 0  # 记录天数，以指导子仓位轮动
    g.fn = 250  # 过滤上市不足250个交易日的股票
    g.watch_days = 10  # 观察连板的持续天数
    g.code_list = ['None']  # 记录每天信号股票，去重使用
    g.count_list = []  # 记录每日最大连板数，用于计算情绪周期
    g.emo_cycle = 3  # 情绪周期长度
    g.p = 0.8  # 子账户仓位控制比例
    g.initial_cash = context.portfolio.available_cash / 2  # 每期可用总资金
    # 设置交易时间
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(get_stock_list, time='15:30', reference_security='000300.XSHG')
```

  * **功能说明** : 初始化策略的基本参数，包括交易成本、子账户配置、情绪周期设置等。并设置每日的交易和选股时间。

  * **关键逻辑** :

    * set_subportfolios 用于配置双子账户，每个账户初始资金为总资金的一半，以便在不同情绪周期内进行轮动操作。

2\. 选股函数 (get_stock_list)

```python
def get_stock_list(context):
    stat_date = context.current_dt.strftime('%Y-%m-%d')
    df = get_all_securities(types=['stock'], date=stat_date)
    stock_list = list(df.index)
    stock_list = filter_new_stock(context, stock_list, stat_date, g.fn)
    stock_list0 = filter_st_stock(context, stock_list, stat_date)
    stock_list1 = filter_hl_stock(context, stock_list0, stat_date)
    if len(stock_list1) != 0:
        stock_list = stock_list1
    else:
        stock_list = stock_list0
    continue_count_df = []
    days_count = g.watch_days + 1
    while len(continue_count_df) == 0:
        days_count -= 1
        if days_count <= 1:
            break
        else:
            MKT_df = limit_count(context, stock_list, stat_date, days_count)
            continue_count_df = MKT_df[MKT_df['count'] == days_count]
    if days_count > 1:
        smallest_stock = get_smallest(context, list(continue_count_df['code']), stat_date)
        count_df = continue_count_df.copy()
        count_df.index = count_df['code']
        limit_counts = count_df.loc[smallest_stock]['count']
        g.count_list.append(limit_counts)
        if len(g.count_list) > (g.emo_cycle - 1):
            emotion = g.count_list[-1] - max(g.count_list[-g.emo_cycle:])
        else:
            emotion = -100
    else:
        limit_counts = 0
        emotion = -100
        g.count_list.append(limit_counts)
    if emotion == 0:
        g.code_list.append(smallest_stock)
        if g.code_list[-1] != g.code_list[-2]:
            g.buy_stock = smallest_stock
        else:
            g.buy_stock = 0
    else:
        g.buy_stock = 0
    if g.buy_stock != 0:
        q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code == g.buy_stock)
        df = get_fundamentals(q, date=stat_date)
        df = df[(df['circulating_market_cap'] > 20) & (df['circulating_market_cap'] < 80)]
        if len(df) == 0:
            g.buy_stock = 0
    if g.buy_stock != 0:
        if (limit_counts < 4) or (limit_counts > 8):
            g.buy_stock = 0
    print(g.buy_stock)
    return g.buy_stock
```

  * **功能说明** : 该函数用于筛选符合条件的股票，结合连板数、市值等多因子条件，最终确定当天的目标股票。

  * **关键逻辑** :

    * emotion 指标用于衡量市场情绪，通过计算当前连板数与情绪周期内的最大连板数的差值，判断市场情绪是否适合进行交易。

3\. 交易函数 (my_trade)

```python
def my_trade(context):
    g.count_days += 1
    hold_list0 = []
    position_dict0 = context.subportfolios[0].long_positions
    for position in list(position_dict0.values()):
        hold_list0.append(position.security)
    hold_list1 = []
    position_dict1 = context.subportfolios[1].long_positions
    for position in list(position_dict1.values()):
        hold_list1.append(position.security)
    if g.count_days % 120 == 1:
        if len(hold_list0) != 0:
            for stock in hold_list0:
                order_target_value(stock, 0, pindex=0)
        elif len(hold_list1) != 0:
            for stock in hold_list1:
                order_target_value(stock, 0, pindex=1)
        else:
            print('账户再平衡前没有持仓')
        g.initial_cash = context.portfolio.available_cash / 2
        cash0 = context.subportfolios[0].available_cash
        cash1 = context.subportfolios[1].available_cash
        to_transfer_cash = (max(cash0, cash1) - min(cash0, cash1)) / 2
        if cash0 > cash1:
            transfer_cash(from_pindex=0, to_pindex=1, cash=to_transfer_cash)
        else:
            transfer_cash(from_pindex=1, to_pindex=0, cash=to_transfer_cash)
    target_cash = g.p * g.initial_cash
    if g.count_days % 3 == 1:
        if len(hold_list1) != 0:
            order_target_value(hold_list1[0], 0, pindex=1)
        else:
            print('账户2无持仓')
        if g.buy_stock != 0:
            cash0 = context.subportfolios[0].available_cash
            if cash0 >= target_cash:
                order_target_value(g.buy_stock, target_cash, pindex=0)
            else:
                order_target_value(g.buy_stock, cash0, pindex=0)
        else:
            print('未选出股票')
    elif g.count_days % 3 == 2:
        if g.buy_stock != 0:
 cash1 = context.subportfolios[1].available_cash
            if cash1 >= target_cash:
                order_target_value(g.buy_stock, target_cash, pindex=1)
            else:
                order_target_value(g.buy_stock, cash1, pindex=1)
        else:
            print('未选出股票')
    elif g.count_days % 3 == 0:
        if len(hold_list0) != 0:
            order_target_value(hold_list0[0], 0, pindex=0)
        else:
            print('账户1无持仓')
        if g.buy_stock != 0:
            cash0 = context.subportfolios[0].available_cash
            if cash0 >= target_cash:
                order_target_value(g.buy_stock, target_cash, pindex=0)
            else:
                order_target_value(g.buy_stock, cash0, pindex=0)
        else:
            print('未选出股票')
```

  * **功能说明** : 根据策略选出的股票执行交易操作，使用双子账户在情绪周期内进行轮动操作，并管理每个子账户的仓位。

  * **关键逻辑** :

    * 每隔一段时间（120天）执行账户再平衡，确保双子账户的资金分布合理。

    * 每个子账户根据情绪周期的轮动，在特定日期进行买卖操作，确保资金的有效利用。

4\. 工具函数

  * filter_st_stock：过滤ST股票。

  * filter_new_stock：过滤上市时间不足250天的新股。

  * filter_hl_stock：保留昨日涨停的股票。

  * limit_count：计算股票在观察期内的涨跌停次数。

  * get_smallest：在符合条件的股票中选择市值最小的股票。

# 策略总结

**多因子动态情绪轮动策略** 通过市场情绪和多个基本面指标筛选出具有投资潜力的股票，并结合双子账户的动态轮动策略，在不同行情下灵活调整持仓，确保投资的稳健性和收益的稳定性。该策略适合具有一定风险承受能力，并希望通过多因子分析和市场情绪把握投资机会的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
