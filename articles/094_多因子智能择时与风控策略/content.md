# 94、多因子智能择时与风控策略

# 策略概述

**多因子智能择时与风控策略** 是一种结合多因子选股、市场牛熊市判断以及动态仓位管理的量化交易策略。该策略利用多因子筛选模型从市场中筛选出潜力股票，并根据市场的牛熊市状态调整仓位，同时设有完善的风控机制以应对市场波动。策略注重在牛市中积极进攻，在熊市中谨慎防守，力求在不同市场环境下保持较为稳健的收益。

# 策略详细介绍

  1. **策略思想** ：

     * **多因子选股** ：基于市值、成交量、价格、涨幅等多个因子，对股票进行综合评分和筛选，以选出优质的投资标的。

     * **市场择时** ：通过对市场指数（如上证指数）的均线分析判断市场处于牛市或熊市，从而决定持仓策略。

     * **动态仓位管理** ：在不同市场状态下，动态调整持仓的仓位比例，在牛市中积极参与市场，在熊市中控制风险。

     * **风控机制** ：策略包含个股止损机制和整体回撤控制，以避免市场大幅波动带来的损失。

  2. **关键要素** ：

     * **因子权重配置** ：通过配置不同的因子权重，增强选股模型的有效性和稳健性。

     * **择时信号** ：根据市场指数的均线交叉信号，判断市场趋势，并决定是否进行全面持仓或降低仓位。

     * **风险管理** ：设置个股止损和整体回撤机制，以保护资本免受大幅损失。

# 策略代码与功能说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    set_option('use_real_price', True)
    log.set_level('order', 'error')
    log.set_level('history', 'error')
    myscheduler()
    g.isbull = False  # 是否牛市
    g.chosen_stock_list = []  # 存储选出来的股票
    g.nohold = True  # 空仓专用信号
    g.sold_stock = {}  # 近期卖出的股票及卖出天数
```

  * **功能说明** : 初始化策略的基本参数，包括设置交易选项、牛熊市初始状态、选股列表、空仓信号等。

  * **关键逻辑** :

    * 使用 set_option 设置真实价格交易模式。

    * 初始化变量以跟踪牛熊市状态、选股列表、空仓状态和卖出股票记录。

2\. 设置策略参数 (set_param)

```python
def set_param():
    g.stocknum = 4  # 理想持股数量
    g.bearpercent = 0.3  # 熊市仓位
    g.bearposition = True  # 熊市是否持仓
    g.sellrank = 10  # 排名多少位之后(不含)卖出
    g.buyrank = 9  # 排名多少位之前(含)可以买入
    g.tradeday = 300  # 上市天数
    g.increase1d = 0.087  # 前一日涨幅
    g.tradevaluemin = 0.01  # 最小流通市值 单位（亿）
    g.tradevaluemax = 1000  # 最大流通市值 单位（亿）
    g.pbmin = 0.5  # 最小市净率
    g.pbmax = 3.5  # 最大市净率
    g.weights = [5, 5, 8, 4, 10]  # 排名条件及权重
    g.MA = ['000001.XSHG', 10]  # 均线择时
    g.choose_time_signal = True  # 启用择时信号
    g.threshold = 0.003  # 牛熊切换阈值
    g.buyagain = 5  # 再次买入的间隔时间
```

  * **功能说明** : 设置策略的各项参数，包括持股数量、熊市仓位、筛选条件、择时信号、因子权重等。

  * **关键逻辑** :

    * 通过设定不同的参数，灵活配置策略的选股、择时、风险管理等模块。

3\. 获取股票涨幅 (get_growth_rate)

```python
def get_growth_rate(code, n=20):
    lc = get_close_price(code, n)
    c = get_close_price(code, 1, '1m')
    if not isnan(lc) and not isnan(c) and lc != 0:
        return (c - lc) / lc
    else:
        log.error("数据非法, code: %s, %d日收盘价: %f, 当前价: %f" % (code, n, lc, c))
        return 0
```

  * **功能说明** : 计算股票 n 日以来的涨幅，作为选股因子之一。

  * **关键逻辑** :

    * 通过获取过去 n 日的收盘价与当前价的差值，计算涨幅，确保输入的数据有效性。

4\. 筛选股票池 (get_stock_list)

```python
def get_stock_list(context):
    df = get_fundamentals(query(valuation.code).filter(valuation.pb_ratio.between(g.pbmin, g.pbmax)).order_by(valuation.circulating_market_cap.asc()).limit(1000)).dropna()
    stock_list = list(df['code'])
    stock_list = filter_gem_stock(context, stock_list)
    stock_list = filter_st_stock(stock_list)
    stock_list = filter_paused_stock(stock_list)
    stock_list = filter_limitup_stock(context, stock_list)
    stock_list = filter_new_stock(context, stock_list)
    stock_list = filter_increase1d(stock_list)
    stock_list = filter_buyagain(stock_list)
    return stock_list
```

  * **功能说明** : 筛选出符合条件的股票池，作为后续进一步筛选的基础。

  * **关键逻辑** :

    * 筛选过程中，依次过滤创业板股票、ST股、停牌股、涨停股、新股、前一日涨幅过高的股票以及近期卖出过的股票。

5\. 选股排序 (get_stock_rank_m_m)

```python
def get_stock_rank_m_m(stock_list):
    rank_stock_list = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.circulating_market_cap).filter(valuation.code.in_(stock_list)).order_by(valuation.circulating_market_cap.asc()).limit(100))
    volume5d = [attribute_history(stock, 1200, '1m', 'volume', df=False)['volume'].sum() for stock in rank_stock_list['code']]
    increase60d = [get_growth_rate60(stock) for stock in rank_stock_list['code']]
    current_price = [get_close_price(stock, 1, '1m') for stock in rank_stock_list['code']]
    min_price = min(current_price)
    min_increase60d = min(increase60d)
    min_circulating_market_cap = min(rank_stock_list['circulating_market_cap'])
    min_market_cap = min(rank_stock_list['market_cap'])
    min_volume = min(volume5d)
    totalcount = [[i, math.log(min_volume / volume5d[i]) * g.weights[3] + math.log(min_price / current_price[i]) * g.weights[2] + math.log(min_circulating_market_cap / rank_stock_list['circulating_market_cap'][i]) * g.weights[1] + math.log(min_market_cap / rank_stock_list['market_cap'][i]) * g.weights[0] + math.log(min_increase60d / increase60d[i]) * g.weights[4]] for i in rank_stock_list.index]
    totalcount.sort(key=lambda x: x[1])
    return [rank_stock_list['code'][totalcount[-1-i][0]] for i in range(min(g.sellrank, len(rank_stock_list)))]
```

  * **功能说明** : 对筛选出的股票池进行多因子排序，选出符合策略的前 g.sellrank 只股票。

  * **关键逻辑** :

    * 通过对多个因子的计算并赋予权重，综合评分排序，并选出最优股票。

6\. 动态调仓 (my_adjust_position)

```python
def my_adjust_position(context, hold_stocks):
    if g.choose_time_signal and (not g.isbull):
        free_value = context.portfolio.total_value * g.bearpercent
        maxpercent = 1.3 / g.stocknum * g.bearpercent
    else:
        free_value = context.portfolio.total_value
        maxpercent = 1.3 / g.stocknum
    buycash = free_value / g.stocknum
    for stock in context.portfolio.positions.keys():
        current_data = get_current_data()
        nosell_1 = context.portfolio.positions[stock].
price >= current_data[stock].high_limit
        sell_2 = stock not in hold_stocks
        if sell_2 and not nosell_1:
            close_position(stock)
        else:
            current_percent = context.portfolio.positions[stock].value / context.portfolio.total_value
            if current_percent > maxpercent:
                order_target_value(stock, buycash)
```

  * **功能说明** : 根据当前市场状态调整持仓，确保仓位在合理范围内，并避免集中度过高。

  * **关键逻辑** :

    * 在牛市和熊市中分别设置不同的持仓比例，动态调整持仓的股票权重，避免过度集中和风险暴露。

7\. 风控管理 (risk_management)

```python
def risk_management(context):
    if context.current_dt.year < 2020:
        return
    for stock in context.portfolio.positions.keys():
        fuying = context.portfolio.positions[stock].price / context.portfolio.positions[stock].avg_cost - 1
        current_data = get_current_data()
        nosell_1 = context.portfolio.positions[stock].price >= current_data[stock].high_limit
        if fuying < -0.065 and not nosell_1:
            close_position(stock)
    if context.portfolio.total_value < max(g.value) * 0.70:
        g.stop_run = True
        log.info("当前策略净值回撤达到30%, 策略可能失效，需要清仓后做重新评估")
        for stock in context.portfolio.positions.keys():
            if not nosell_1:
                close_position(stock)
```

  * **功能说明** : 实施个股止损和整体回撤管理，确保策略在市场剧烈波动时仍能有效控制风险。

  * **关键逻辑** :

    * 当个股浮亏超过 6.5% 或者整体账户回撤超过 30% 时，触发止损和清仓机制，防止进一步亏损。

# 总结

该策略通过多因子选股模型和市场择时相结合，搭配灵活的仓位管理和风控机制，力求在不同市场环境下保持收益的稳定性和可持续性。策略的复杂度适中，适合具有一定市场理解能力和风险承受能力的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
