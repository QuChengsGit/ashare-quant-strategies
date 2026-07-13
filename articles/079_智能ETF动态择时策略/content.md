# 79、智能ETF动态择时策略

# 策略概述

**智能ETF动态择时策略** 是一种基于技术指标的ETF择时策略。策略核心在于通过对市场主要指数的周期动量与涨跌幅度的分析，动态调整ETF的持仓，以应对市场的变化。策略在特定市场条件下做出买入或清仓的决策，从而最大化收益并降低风险。

### 功能代码与详细说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_option('order_volume_ratio', 0.1)
    set_benchmark('000300.XSHG')
    set_slippage(FixedSlippage(0.001))
    set_order_cost(OrderCost(close_tax=0.000, open_commission=0.00006, close_commission=0.00006, min_commission=0), type='fund')
    # 策略参数初始化
    g.dapan_threshold = 0
    g.signal = 'BUY'
    g.lag = 20
    g.decrease_days = 0
    g.increase_days = 0
    g.unit = '30m'
    # 主要指数列表和ETF对照表
    g.zs_list = ['000001.XSHG', '399001.XSHE', '399006.XSHE', '000852.XSHG', '000015.XSHG']
    g.ETF_list = {
        '399905.XSHE':'159902.XSHE',
        '399632.XSHE':'159901.XSHE',
        '000016.XSHG':'510050.XSHG',
        '000010.XSHG':'510180.XSHG',
        '000852.XSHG':'512100.XSHG',
        '399295.XSHE':'159966.XSHE',
        '399958.XSHE':'159967.XSHE',
        '000015.XSHG':'510880.XSHG',
        '399324.XSHE':'159905.XSHE',
        '399006.XSHE':'159915.XSHE',
        '000300.XSHG':'510300.XSHG',
        '000905.XSHG':'510500.XSHG',
        '399673.XSHE':'159949.XSHE',
        '000688.XSHG':'588000.XSHG'
    }
    g.not_ipo_list = g.ETF_list.copy()
    g.available_indexs = []
    run_daily(check_etf, time='9:15')
    run_daily(check_trade, time='11:15')
```

  * **功能说明** : 初始化策略时设置全局参数，包括交易滑点、基准、交易成本等。同时设置了策略的核心参数，如持仓调整逻辑、指数列表和对应的ETF对照表。

  * **关键参数** :

    * g.dapan_threshold: 市场涨幅阈值，超过该值时触发买入信号。

    * g.unit: BBI动量计算的时间周期单位。

2\. 获取交易日期函数 (get_N_trade_date)

```python
def get_N_trade_date(date, N, is_before=True):
    all_date = pd.Series(get_all_trade_days())
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    if isinstance(date, datetime.datetime):
        date = date.date()
    if is_before:
        return all_date[all_date <= date].tail(N).values[0]
    else:
        return all_date[all_date >= date].head(N).values[-1]
```

  * **功能说明** : 获取指定日期之前或之后N个交易日的日期，主要用于判断ETF是否已上市达到一定天数。

3\. 检查ETF上市函数 (check_etf)

```python
def check_etf(context):
    if len(g.not_ipo_list) == 0:
        return
    idxs = []
    yesterday = context.previous_date
    list_date = get_N_trade_date(yesterday, g.lag)
    all_funds = get_all_securities(types='fund', date=yesterday)
    all_idxes = get_all_securities(types='index', date=yesterday)
    for idx in g.not_ipo_list:
        if idx in all_idxes.index:
            if all_idxes.loc[idx].start_date <= list_date:
                symbol = g.not_ipo_list[idx]
                if symbol in all_funds.index:
                    if all_funds.loc[symbol].start_date <= list_date:
                        g.available_indexs.append(idx)
                        idxs.append(idx)
    for idx in idxs:
        del g.not_ipo_list[idx]
    log.info('输出不可交易基金列表：')
    log.info(g.not_ipo_list)
```

  * **功能说明** : 检查策略中ETF的上市时间，确保ETF在满足上市时间条件后才能进行交易。

4\. 分析市场并执行交易 (check_trade)

```python
def check_trade(context):
    log.info("-----今天的交易开始了-----------------------------------------")
    df_index = pd.DataFrame(columns=['指数代码', '周期动量'])
    df_incre = pd.DataFrame(columns=['大盘代码','周期涨幅','当前价格'])
    BBI2 = BBI(g.available_indexs,
               check_date=context.current_dt,
               timeperiod1=3,
               timeperiod2=6,
               timeperiod3=12,
               timeperiod4=24,
               unit = g.unit,
               include_now=True)
    for index in g.available_indexs:
        df_close = get_bars(index, 1, g.unit, ['close'], end_dt=context.current_dt, include_now=True)['close']
        val = BBI2[index]/df_close[0]
        df_index = df_index.append({'指数代码': index, '周期动量': val}, ignore_index=True)
    df_index.sort_values(by='周期动量', ascending=False, inplace=True)
    log.info("输出排序后的指数代码和周期动量")
    log.info(df_index)
    target = df_index['指数代码'].iloc[-1]
    target_bbi = df_index['周期动量'].iloc[-1]
    for index in g.zs_list:
        df_close = get_bars(index, 2, '1d', ['close'], end_dt=context.current_dt, include_now=True)['close']
        if len(df_close) > 1:
            increase = (df_close[1] - df_close[0]) / df_close[0]
            df_incre = df_incre.append({'大盘指数': index, '周期涨幅': increase, '当前数值': df_close[0]}, ignore_index=True)
    df_incre.sort_values(by='周期涨幅', ascending=False, inplace=True)
    log.info("输出大盘数据")
    log.info(df_incre)
    today_increase = df_incre['周期涨幅'].iloc[0]
    today_index_code = df_incre['大盘代码'].iloc[0]
    today_index_close = df_incre['当前数值'].iloc[0]
    if(today_increase > g.dapan_threshold and target_bbi < 1):
        g.signal = 'BUY'
        g.increase_days += 1
    else:
        g.signal = 'CLEAR'
        g.decrease_days += 1
    holdings = set(context.portfolio.positions.keys())
    log.info("-------------increase_days----------- %s" % (g.increase_days))
    log.info("-------------decrease_days----------- %s" % (g.decrease_days))
    target_etf = g.ETF_list[target]
    if(g.signal == 'CLEAR'):
        for etf in holdings:
            log.info("----~~~---指数集体下跌，卖出---~~~~~~-------- %s" % (etf))
            order_target(etf, 0)
            return
    else:
        for etf in holdings:
            if (etf == target_etf):
                log.info('相同etf，不需要调仓！@')
                return
            else:
                order_target(etf, 0)
                log.info("------------------调仓卖出----------- %s" % (etf))
        log.info("------------------买入----------- %s" % (target))
        order_value(target_etf,context.portfolio.available_cash)
```

  * **功能说明** : 分析市场指数的周期动量与涨跌幅，判断是否需要调仓或清仓。策略会根据市场信号做出买入或卖出的决定。

  * **关键逻辑** :

    * **BBI分析** : 通过BBI（多空均线指标）和周期涨幅判断市场趋势。

    * **交易信号** : 当符合特定条件时，发出买入或清仓信号。

5\. 支持函数与工具函数

  * **获取交易日期 (get_N_trade_date)** : 用于获取指定日期之前或之后的交易日期。

  * **BBI指标** : 计算多空均线指标，用于判断市场趋势。

### 策略亮点

  * **动态择时** : 结合BBI与市场涨幅，策略能够有效识别市场的多空趋势，从而做出动态调整。

  * **ETF轮动** : 根据市场条件轮动持仓ETF，优化收益。

  * **灵活调仓** : 通过精确的调仓逻辑，策略在不同市场条件下能够灵活应对，实现稳健收益。

### 适用场景

本策略适用于希望通过ETF投资获得市场平均收益的投资者，特别是那些关注市场趋势并希望在市场波动中保持灵活性的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
