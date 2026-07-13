# 90、多因子择时均衡买入策略

# 策略概述

**多因子择时均衡买入策略** 是一种基于多种技术指标进行择时并筛选优质股票的策略。策略首先通过多因子筛选，如均线交叉、MACD、资金流向等指标，挑选出具有上涨潜力的股票，并在开盘时根据预定的仓位限制自动买入或卖出。策略力求通过精准的技术分析和严谨的择时机制，在市场中捕捉优质买入机会并避免风险。

策略详细介绍

  1. **策略思想** ：

     * **多因子筛选** ：策略通过一系列技术指标（如均线交叉、MACD信号、资金流向等）筛选出潜力股，并在开盘前确定最终的买入候选名单。

     * **自动化交易** ：策略在开盘时根据持仓情况和买入名单，自动执行买入和卖出操作，确保组合在任何市场环境下都能及时调整仓位。

     * **持仓限制** ：策略严格控制持仓股票的数量，通过预设的持仓限制避免过度集中风险。

  2. **关键要素** ：

     * **均线策略** ：通过分析股票的短期（5日、10日）与长期（20日、30日）均线的交叉情况，判断股票的价格走势。

     * **MACD信号** ：结合MACD指标的变化判断市场情绪，挑选出具有上涨潜力的股票。

     * **资金流向分析** ：通过分析资金流向的变化来确认资金的进出情况，辅助判断股票的买入或卖出信号。

     * **开盘时的自动化执行** ：策略在开盘时自动执行选股和交易指令，确保策略的及时性。

# 策略代码与功能说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    enable_profile()  # 启用性能分析
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 开启动态复权模式(真实价格)
    set_option("avoid_future_data", True)  # 关闭未来函数
    set_slippage(FixedSlippage(0))  # 将滑点设置为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本万分之三
    g.buy_stock_limit = 1  # 股票购买限制，设置为1表示每次只买入1支股票
```

  * **功能说明** : 初始化策略参数，包括基准、交易成本、滑点等设置。并设定每次最大买入股票数量为1。

  * **关键逻辑** :

    * set_benchmark('000300.XSHG') 将沪深300设定为策略的基准指数。

    * g.buy_stock_limit = 1 限制每次最多持有1支股票，确保集中投资。

2\. 开盘前的选股与择时 (before_trading_start)

```python
def before_trading_start(context):
    initHandleParam()  # 初始化全局变量
    prev_trade_day = context.previous_date  # 获取前一个交易日
    stock_pool = get_all_securities(['stock'], date=prev_trade_day)  # 获取所有股票池
    stock_list = filter_stock(stock_pool)  # 过滤掉不符合条件的股票
    # 获取均线数据
    p1_ma5 = get_stock_price(stock_list, prev_trade_day, 5).groupby('code').mean()
    p1_ma10 = get_stock_price(stock_list, prev_trade_day, 10).groupby('code').mean()
    p1_ma20 = get_stock_price(stock_list, prev_trade_day, 20).groupby('code').mean()
    p1_ma30 = get_stock_price(stock_list, prev_trade_day, 30).groupby('code').mean()
    p2_ma5 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 5).groupby('code').mean()
    p2_ma10 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 10).groupby('code').mean()
    p2_ma20 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 20).groupby('code').mean()
    p2_ma30 = get_stock_price(stock_list, getday3(prev_trade_day, -1), 30).groupby('code').mean()
    # 均线与量价指标的多因子筛选
    dx1 = []
    for stock in stock_list:
        if p1_ma5['close'][stock] < p1_ma10['close'][stock] \
                and p2_ma5['close'][stock] > p2_ma10['close'][stock] \
                and p2_ma5['volume'][stock] > p2_ma10['volume'][stock] \
                and (p1_ma5['volume'][stock] * 1.2) > p1_ma10['volume'][stock] \
                and p1_ma20['close'][stock] > p2_ma20['close'][stock] \
                and p1_ma30['close'][stock] > p2_ma30['close'][stock]:
            dx1.append(stock)
    print('dx1可选股票%s支.' % (len(dx1)))
    # MACD信号筛选
    dx2 = []
    macd_dif, macd_dea, macd_macd = MACD(security_list=dx1, check_date=prev_trade_day, SHORT=12, LONG=26, MID=9, unit='1d')
    for stock in dx1:
        if macd_dif[stock] > 0 and macd_dea[stock] > 0 and 0 > macd_dea[stock] - macd_dif[stock] > -0.1:
            dx2.append(stock)
    print('dx2可选股票%s支' % (len(dx2)))
    # 资金流向筛选
    dx3 = []
    for stock in dx2:
        p1_flow = get_money_flow(security_list=stock, end_date=prev_trade_day, count=1, fields=['change_pct'])
        p2_flow = get_money_flow(security_list=stock, end_date=getday3(prev_trade_day, -1), count=1, fields=['change_pct'])
        if len(p1_flow['change_pct']) == 0 or len(p2_flow['change_pct']) == 0:
            continue
        if (p1_flow['change_pct'][0] > 0 and p2_flow['change_pct'][0] < 0) \
                or (p1_flow['change_pct'][0] < 0 and p2_flow['change_pct'][0] > 0):
            dx3.append(stock)
    print('dx3可选股票%s支' % (len(dx3)))
    # 最终筛选出满足条件的股票列表
    dx5 = []
    current_data = get_current_data()
    for stock in dx3:
        p1_1 = get_price(security=stock, end_date=prev_trade_day, frequency='1d', fields=['close'],
                         panel=False, count=1, skip_paused=True)
        if p1_1['close'][0] <= current_data[stock].day_open:
            continue
        dx5.append(stock)
    print('dx5可选股票%s支' % (len(dx5)))
    g.buy_list = dx5
    g.buy_list.sort()
    print('%s:共找到%d只股票可以购买.%s' % (context.current_dt, len(g.buy_list), g.buy_list))
```

  * **功能说明** : 开盘前执行多因子筛选，依次根据均线交叉、MACD信号和资金流向，筛选出最终的买入候选股票。

  * **关键逻辑** :

    * 多重技术指标的联合筛选确保选出的股票具有较高的上涨潜力。

    * g.buy_list 存储筛选出的候选股票列表，供开盘时进行交易。

3\. 开盘时的交易执行 (handle_data)

```python
def handle_data(context, data):
    current_data = get_current_data()
    # 卖出条件
    for stock in context.portfolio.positions.keys():
        price = data[stock].close
        if context.portfolio.positions[stock].closeable_amount == 0 \
                or current_data[stock].low_limit == price \
                or current_data[stock].high_limit == price:
            continue
        print('%s卖出(自动):自动卖出:成本价:%s,当前价:%s' % (stock, context.portfolio.positions[stock].avg_cost, price))
        sell_stock(stock, 0)
    # 判断是否买满
    if g.buy_stock_limit <= len(context.portfolio.positions.keys()):
        return
    # 买入条件
    for stock in g.buy_list:
        price = data[stock].close
        if context.portfolio.available_cash < (price * 100) \
                or current_data[stock].low_limit == price \
                or current_data[stock].high_limit == price \
                or stock in context.portfolio.positions.keys():
            continue
        print('%s买入(自动):自动买入:当前价:%s' % (stock, price))
        buy_stock(context, stock)
        break
```

  * **功能说明** : 开盘时执行自动买入和卖出操作。首先检查是否需要卖出股票，然后根据筛选出的买入列表，执行买入操作。

  * **关键逻辑** :

    * sell_stock 执行卖出操作，自动卖出不符合条件的股票。

    * buy_stock 根据可用资金和筛选条件自动买入股票，确保投资组合的及时调整。

4\. 公共函数模块

```python
def initHandleParam():
    g.buy_list = []
def get_stock_price(stock_list, ed, days):
    stock_price = get_price(security=stock_list, end_date=ed, frequency='1d', fields=['close', 'volume'],
                            panel=False, count=days, skip_paused=True)
    return stock_price
def getday3(d, step):
    day = d + datetime.timedelta(step)
    return day
def buy_stock(context, stock):
    need_count = g.buy_stock_limit - len(context.portfolio.positions.keys())
    if need_count == 0:
        return
    buy_cash = context.portfolio.available_cash / need_count
    order_value(stock, buy_cash)
def sell_stock(stock, value):
    order_target(stock, value)
```

  * **功能说明** : 提供一些常用的辅助函数，用于计算日期、获取股票价格、买入和卖出股票等操作。

  * **关键逻辑** :

    * getday3 计算基于当前日期的时间偏移，用于日期处理。

    * buy_stock 计算每次买入的金额并执行买入操作。

    * sell_stock 根据传入的价值参数执行卖出操作。

# 策略总结

**多因子择时均衡买入策略** 通过精细化的多因子技术分析，筛选出市场中具有短期上涨潜力的股票，并结合严格的交易限制和自动化执行，实现了在动态市场中的稳健投资。策略特别适合在波动性较大的市场中寻找交易机会，同时通过限制持仓数量来规避集中风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
