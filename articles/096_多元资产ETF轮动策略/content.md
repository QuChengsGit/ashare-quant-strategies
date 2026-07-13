# 96、多元资产ETF轮动策略

# 策略概述

**多元资产ETF轮动策略** 是一种基于市场动量和均线状态的跨市场资产配置策略。该策略通过定期筛选表现强劲的ETF品种（包括A股指数、全球股指、国内期货、全球期货、REITs），并根据市场表现进行轮动投资。策略旨在利用不同资产类别间的轮动效应，在不同市场环境下优化资产配置，获取相对稳定的收益。

# 策略详细介绍

  1. **策略思想** ：

     * **市场轮动** ：通过定期筛选表现强劲的ETF品种，捕捉市场热点，动态调整资产配置，最大化投资组合的收益。

     * **多元资产配置** ：策略覆盖多个资产类别（如A股、全球股指、国内外期货、REITs），通过跨市场分散投资，降低单一市场波动对组合收益的影响。

     * **动量与均线策略** ：结合动量（过去一段时间的价格涨幅）和均线状态（当前价格与均线的关系）进行筛选，优先选择趋势向上的资产。

     * **自动化交易与风险控制** ：策略自动化运行，每日计算交易信号并执行买卖操作，确保在市场环境变化时快速响应。

# 策略代码与功能说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    g.purchases = []
    g.sells = []
    set_params()
    set_option("avoid_future_data", True)
    set_option('use_real_price', True)
    set_benchmark('000300.XSHG')
    log.set_level('order', 'error')
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.00005, close_commission=0.00005, min_commission=0), type='stock')
    run_daily(before_market_open, time='21:00', reference_security='000300.XSHG')
    run_daily(get_signal, time='21:00')
    run_daily(ETF_trade, time='9:32')
```

  * **功能说明** : 初始化策略，设定全局参数、交易基准、交易成本和执行时间，确保策略在合适的时间运行并输出有效的交易信号。

  * **关键逻辑** :

    * 设定交易参数和时间调度，确保策略每日能在开盘前后进行信号计算和执行交易。

2\. 设置参数 (set_params)

```python
def set_params():
    g.target_market = '000300.XSHG'
    g.moment_period = 13  # 计算行情趋势的短期均线周期
    g.ma_period = 10      # 计算均线的周期
    g.type_num = 5        # 每次最多选择的资产类别数量
    g.ETF_targets = {
        '000300.XSHG':'510300.XSHG',  # 沪深300
        '399006.XSHE':'159915.XSHE',  # 创业板
        '518880.XSHG':'518880.XSHG',  # 黄金ETF
        '501018.XSHG':'501018.XSHG',  # 南方原油
        '161226.XSHE':'161226.XSHE',  # 白银基金
        # 更多标的...
    }
    g.local_stocks  = ['510300.XSHG', '159915.XSHE']
    g.global_stocks = ['513100.XSHG', '164824.XSHE']
    g.local_futures = ['159980.XSHE', '159981.XSHE']
    g.global_futures = ['161226.XSHE', '518880.XSHG']
    g.REITs = ['180101.XSHE', '180301.XSHE']
    # 打印股票池信息
    stocks_info = "\n股票池:\n"
    for security in g.ETF_targets.values():
        s_info = get_security_info(security)
        stocks_info += "【%s】%s 上市日期:%s\n" % (s_info.code, s_info.display_name, s_info.start_date)
    log.info(stocks_info)
```

  * **功能说明** : 设置策略参数，包括不同资产类别的标的ETF列表和计算市场动量的周期等。

  * **关键逻辑** :

    * 定义多元资产的ETF标的池，确保覆盖广泛的市场，并通过设定计算周期捕捉市场趋势。

3\. 开盘前运行函数 (before_market_open)

```python
def before_market_open(context):
    yesterday = context.previous_date
    list_date = get_before_after_trade_days(yesterday, g.moment_period+1)
    g.ETFList = {}
    all_funds = get_all_securities(types='fund', date=yesterday)
    for idx in g.ETF_targets:
        symbol = g.ETF_targets[idx]
        if symbol in all_funds.index and all_funds.loc[symbol].start_date <= list_date:
            g.ETFList[idx] = symbol
```

  * **功能说明** : 在开盘前筛选出符合条件的ETF标的，将上市时间不足的标的排除，确保仅选择具有足够历史数据的ETF进行交易。

  * **关键逻辑** :

    * 确保参与交易的ETF标的有足够的交易历史，以保证技术分析的可靠性。

4\. 信号获取函数 (get_signal)

```python
def get_signal(context):
    g.df_etf = pd.DataFrame(columns=['基金代码', '基金名称','涨幅','均线状态','股数'])
    total_value = context.portfolio.total_value
    current_time = context.current_dt
    for mkt_idx in g.ETFList:
        security = g.ETFList[mkt_idx]
        etf_name = get_security_info(security).display_name
        price_data = get_price(security, end_date=current_time, frequency='1d', fields=['close'], count=g.moment_period+1)
        now_close = price_data['close'][-1]
        previous_close = price_data['close'][-g.moment_period]
        ma_filter = ta.MA(price_data.close.values, g.ma_period)[-1]
        ma_status = now_close - ma_filter
        moment = (now_close - previous_close) / previous_close * 100
        amount = int(total_value / now_close / g.type_num /100)*100
        g.df_etf = g.df_etf.append({'基金代码': security,
                                    '基金名称': etf_name,
                                    '涨幅': moment,
                                    '均线状态': ma_status,
                                    '股数': amount},
                                   ignore_index=True)
    g.df_etf.sort_values(by='涨幅', axis=0, ascending=False, inplace=True)
    tb = pt.PrettyTable()
    tb.add_column('ETF Code', list(g.df_etf['基金代码']))
    tb.add_column('Name', list(g.df_etf['基金名称']))
    tb.add_column('Moment', list(g.df_etf['涨幅'].values.round(2)))
    tb.add_column('Ma_Status', list(g.df_etf['均线状态'].values.round(2)))
    tb.add_column('Amount', list(g.df_etf['股数']))
    log.info('\n行情统计: \n%s' % tb)
    # 筛选符合条件的标的
    g.df_etf_buy = g.df_etf[(g.df_etf['涨幅'] > 0) & (g.df_etf['均线状态'] > 0)]
    # 根据不同资产类别进行分类
    g.df_local_stocks = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.local_stocks)]
    g.df_global_stocks = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.global_stocks)]
    g.df_local_futures = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.local_futures)]
    g.df_global_futures = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.global_futures)]
    g.df_reits = g.df_etf_buy.loc[g.df_etf_buy['基金代码'].isin(g.REITs)]
    g.holdings = set(context.portfolio.positions.keys())
    g.targets = []
    if len(g.df_local_stocks) > 0:
        g.targets.append(g.df_local_stocks.iloc[0]['基金代码'])
    if len(g.df_global_stocks) > 0:
        g.targets.append(g.df_global_stocks.iloc[0]['基金代码'])
    if len(g.df_local_futures) > 0:
        g.targets.append(g.df_local_futures.iloc[0]['基金代码'])
    if len(g.df_global_futures) > 0:
        g.targets.append(g.df_global_futures.iloc[0]['基金代码'])
    if len(g.df_reits) > 0:
        g.targets.append(g.df_reits.iloc[0]['基金代码'])
    g.sells = [i for i in g.holdings if i not in g.targets]
    g.purchases = [i for
 i in g.targets if i not in g.holdings]
    # 输出交易计划
    content = '交易计划：\n'
    if len(g.sells) > 0:
        tb = pt.PrettyTable()
        df_sells = g.df_etf.loc[g.df_etf['基金代码'].isin(g.sells)]
        tb.add_column('ETF Code', list(df_sells['基金代码']))
        tb.add_column('Name', list(df_sells['基金名称']))
        str_more = '\n计划卖出: \n' + str(tb)
        content += str_more
        log.info(str_more)
    if len(g.purchases) > 0:
        tb = pt.PrettyTable()
        df_purchase = g.df_etf.loc[g.df_etf['基金代码'].isin(g.purchases)]
        tb.add_column('ETF Code', list(df_purchase['基金代码']))
        tb.add_column('Name', list(df_purchase['基金名称']))
        tb.add_column('Amount', list(df_purchase['股数']))
        str_more = '\n计划买入：\n' + str(tb)
        content += str_more
        log.info(str_more)
    if (len(g.sells) == 0) and (len(g.purchases) == 0):
        log.info('\n无交易计划: \n')
    return
```

  * **功能说明** : 计算市场动量和均线状态，并生成当日交易信号。策略根据涨幅和均线状态选择表现最强的资产，并准备买入，同时卖出不再符合条件的资产。

  * **关键逻辑** :

    * 通过动量和均线的组合，筛选出潜在收益较高的ETF，并为交易准备。

    * 根据每个资产类别选择一个表现最强的品种，确保资产多元化。

5\. 交易执行函数 (ETF_trade)

```python
def ETF_trade(context):
    if len(g.sells) > 0:
        for code in g.sells:
            log.info("卖出: %s" % code)
            order_target(code, 0)
    if len(g.purchases) > 0:
        for code in g.purchases:
            log.info('买入: %s' % code)
            order_target(code, g.df_etf[g.df_etf['基金代码'] == code]['股数'].values)
```

  * **功能说明** : 在交易时段内执行买入和卖出操作，调整持仓组合。

  * **关键逻辑** :

    * 自动执行买入和卖出操作，确保持仓组合动态调整，符合当前市场情况。

# 总结

**多元资产ETF轮动策略** 通过筛选各类资产中表现最强的ETF，利用动量和均线策略，动态调整持仓，实现跨市场的稳健投资。这一策略适用于希望在复杂市场环境中获取稳定收益的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
