# 87、月度量化股票筛选与再平衡策略

# 策略概述

**月度量化股票筛选与再平衡策略** 是一个基于预先计算的股票评分数据进行月度再平衡的量化投资策略。该策略每月末重新选择一组评分最高的股票并均匀配置资金，旨在通过定期再平衡获取市场中的超额收益。策略通过加载外部评分数据，根据当月市场环境调整持仓，最大化收益潜力。

# 策略详细介绍

  1. **策略思想** ：

     * **股票评分与筛选** ：利用外部量化模型得出的股票评分数据，每月初选择评分最高的一组股票进行投资。

     * **定期再平衡** ：每月末对持仓进行调整，清空不在评分范围内的股票，并均匀分配资金至新选出的股票组合。

     * **风险控制** ：通过均衡配置和月度调整，平衡收益与风险，避免单一股票的过度集中风险。

  2. **关键要素** ：

     * **评分数据加载** ：策略运行时从外部文件加载预先计算的股票评分数据。

     * **定期再平衡** ：每月末进行持仓调整，根据最新的评分数据重新配置持仓。

     * **交易成本控制** ：设置固定滑点和交易费用，确保交易过程的成本可控。

# 策略代码与功能说明

1\. 初始化函数与全局变量设置 (initialize)

```python
def initialize(context):
    # 设定上证指数作为基准
    set_default_params(context)  # 初始化系统参数
    set_benchmark(g.security)  # 设置基准为沪深300指数
    # 加载评分数据
    g.df_dic = {}
    tmp_df_dic = pickle.loads(read_file('test_predict_300_q.pkl'))
    for dd, df in tmp_df_dic.items():
        if len(df) == 0:
            continue
        g.df_dic[dd.rsplit('-', 1)[0]] = df.sort_values(by='score', ascending=False)
    run_daily(before_market_open, time='before_open')
    run_daily(market_open, time='open', reference_security=g.security)
```

  * **功能说明** : 初始化策略参数、设置基准、加载外部评分数据，并设置每日的运行时间。

  * **关键逻辑** :

    * set_default_params 设置系统参数，如基准和滑点。

    * pickle.loads(read_file('test_predict_300_q.pkl')) 加载外部量化模型计算的股票评分数据。

2\. 系统默认参数设置 (set_default_params)

```python
def set_default_params(context):
    g.security = '000300.XSHG'  # 基准为沪深300指数
    g.quantile = (0, 10)  # 选择评分前10%的股票
    g.if_trade = False  # 标记是否交易
    set_option('use_real_price', True)
    set_slippage(FixedSlippage(0))
```

  * **功能说明** : 设置系统的默认参数，包括基准指数、评分量化区间、滑点等。

  * **关键逻辑** :

    * g.quantile 控制筛选评分的前 10% 股票作为目标投资组合。

3\. 月末交易日判断 (before_market_open)

```python
def before_market_open(context):
    # 获得当前日期
    rebalance_day = context.current_dt.date()
    next_day = shift_trading_day(rebalance_day, 1)
    if next_day.month != rebalance_day.month:
        if next_day.day < rebalance_day.day:
            log.info(f'############## trade day：{str(rebalance_day)} ##############')
            g.if_trade = True
```

  * **功能说明** : 判断当前交易日是否为月末交易日，并在月末标记是否进行持仓调整。

  * **关键逻辑** :

    * shift_trading_day 函数用于获取下一交易日的日期，通过比较月份判断是否为月末交易日。

4\. 市场开盘执行交易 (market_open)

```python
def market_open(context):
    tar_mon = context.current_dt.date().strftime('%Y-%m')
    if g.if_trade is True:
        if tar_mon in g.df_dic:
            log.info(f'############## tar mon：{str(tar_mon)} today: {str(context.current_dt.date())} ##############')
            stock_df = g.df_dic[tar_mon]
            rebalance(context, stock_df)
        g.if_trade = False
```

  * **功能说明** : 在月初的第一个交易日进行持仓调整，加载当月的评分数据并执行再平衡。

  * **关键逻辑** :

    * rebalance 函数执行持仓调整，根据评分数据买入评分前 10% 的股票，并卖出不再持有的股票。

5\. 再平衡持仓 (rebalance)

```python
def rebalance(context, stock_df):
    # 每只股票购买金额
    total_value = context.portfolio.total_value
    stock_list = stock_df['name'][int(len(stock_df) * g.quantile[0]/100) : int(len(stock_df) * g.quantile[1]/100)].tolist()
    tar_pos = total_value / len(stock_list)
    # 获取股票名称
    name_list = [get_security_info(it).display_name for it in stock_list]
    log.info(f'############## len: {len(stock_list)}, \n tar_pos: {tar_pos}, \n stock list：{str(stock_list)} \n name list: {str(name_list)} ##############')
    for k1 in context.portfolio.positions.keys():
        if k1 not in stock_list:
            order_target_value(k1, 0)  # 卖出不在新选股列表中的股票
    for k in stock_list:
        order_target_value(k, tar_pos)  # 买入新的目标股票
```

  * **功能说明** : 持仓再平衡逻辑，根据当前评分结果重新分配持仓，卖出不再持有的股票，买入新选出的股票。

  * **关键逻辑** :

    * tar_pos 计算每只股票的目标持仓金额，并将其均匀分配至新选出的股票列表中。

# 策略总结

**月度量化股票筛选与再平衡策略** 通过加载外部评分数据和月度再平衡机制，保持投资组合的持续优化。策略采用量化模型提供的评分进行选股，并在每个月末进行持仓调整，以便最大化投资收益。通过严格的风险控制和交易成本管理，该策略能够适应不同市场环境中的变化，适合寻求稳健增长的长期投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
