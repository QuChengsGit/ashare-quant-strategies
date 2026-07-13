# 26、稳健多因子筛选交易策略

### 策略简介

“稳健多因子筛选交易策略”是一种基于多因子模型的股票筛选和交易策略，旨在通过多维度的股票基本面分析（包括股息率、PEG、股价等因素），严格筛选出具有稳健投资价值的股票。策略使用动态复权价格和严格的交易成本控制，结合多因子筛选和涨停股票的特殊处理，实现一个稳健的股票投资组合。

### 策略结构与功能

### 1. 初始化函数

```python
def initialize(context):
    log.set_level('order', 'error')  # 过滤掉低于error级别的log
    set_option('use_real_price', True)  # 开启动态复权模式
    set_option('avoid_future_data', True)  # 避免未来数据
    set_option('order_volume_ratio', 0.1)  # 交易量不超过实际成交量的10%
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_slippage(PriceRelatedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易成本
    g.stock_num = 20  # 最大持仓股票数量
    g.buylist = []  # 待买入股票列表
    g.high_limit_list = []  # 昨日涨停股票列表
    # 设定定时任务
    run_daily(get_high_limit, time='9:00')  # 每天早上获取昨日涨停股票
    run_monthly(get_stocks, 1, time='10:00')  # 每月第一个交易日筛选股票
    run_monthly(trade_stocks, 1, time='14:55')  # 每月第一个交易日执行交易
    run_monthly(show_cap, 1, time='16:00')  # 每月第一个交易日收盘后输出市值等信息
    run_daily(check_high_limit, time='14:40')  # 每日下午检查昨日涨停股票
```

  * **功能说明** :

    * 初始化策略的各项设置，包括交易成本、滑点、全局变量以及定时任务的设定。

    * 策略通过定时任务在指定的时间点执行相应的操作，如筛选股票、交易、检查涨停股票等。

### 2. 获取股票列表

```python
def get_stocks(context):
    by_date = context.previous_date - datetime.timedelta(days=180)
    stocks = get_all_securities(date=by_date).index.tolist()
    stocks = filter_all_stocks(context, stocks)
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    stocks = get_peg(context, stocks)
    stocks = filter_highprice_stock(context, stocks)
    g.buylist = stocks[:g.stock_num]
```

  * **功能说明** :

    * 策略根据多重条件（包括股票上市时间、基本面数据、股息率、PEG、股价等）筛选股票，并将符合条件的股票列表保存到全局变量 g.buylist 中，供后续交易使用。

### 3. 交易股票

```python
def trade_stocks(context):
    cdata = get_current_data()
    # 卖出不在待买入列表中的股票
    for s in context.portfolio.positions:
        if s not in g.buylist:
            log.info('Sell', s, cdata[s].name)
            order_target(s, 0)
    # 买入待买入股票
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        psize = context.portfolio.available_cash / (g.stock_num - position_count)
        for s in g.buylist:
            if s not in context.portfolio.positions:
                log.info('buy', s, cdata[s].name)
                order_value(s, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break
```

  * **功能说明** :

    * 策略首先卖出不在 g.buylist 中的股票，然后将资金平均分配到待买入的股票中，直到达到最大持仓数量。

### 4. 显示市值和股价信息

```python
def show_cap(context):
    current_data = get_current_data()
    hold_stocks = context.portfolio.positions.keys()
    for s in hold_stocks:
        q = query(valuation).filter(valuation.code == s)
        df = get_fundamentals(q)
        log.info(s, current_data[s].name, '市值', df['market_cap'][0], '亿')
        log.info(s, current_data[s].name, '股价', current_data[s].last_price, '元')
```

  * **功能说明** :

    * 输出当前持仓股票的市值和股价信息到日志，帮助投资者跟踪持仓状况。

### 5. 辅助筛选与交易函数

**5.1 计算股息率**

```python
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365)
    interval = 1000
    list_len = len(stock_list)
    q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb).filter(
        finance.STK_XR_XD.a_registration_date >= time0, finance.STK_XR_XD.a_registration_date <= time1,
        finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)]))
    df = finance.run_query(q)
    if list_len > interval:
        for i in range(list_len // interval):
            q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb).filter(
                finance.STK_XR_XD.a_registration_date >= time0, finance.STK_XR_XD.a_registration_date <= time1,
                finance.STK_XR_XD.code.in_(stock_list[interval * (i + 1):min(list_len, interval * (i + 2))]))
            df = df.append(finance.run_query(q))
    dividend = df.fillna(0).groupby('code').sum()
    temp_list = list(dividend.index)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(temp_list))
    cap = get_fundamentals(q, date=time1).set_index('code')
    DR = pd.concat([dividend, cap], axis=1)
    DR['dividend_ratio'] = (DR['bonus_amount_rmb'] / 10000) / DR['market_cap']
    DR.sort_values(by='dividend_ratio', ascending=sort, inplace=True)
    final_list = list(DR.index)[int(p1 * len(DR)):int(p2 * len(DR))]
    return final_list
```

  * **功能说明** :

    * 计算股票的股息率，并根据股息率进行排序和筛选，确保只选择那些具有较高股息率的股票。

**5.2 计算PEG**

```python
def get_peg(context, stocks):
    q = query(valuation.code).filter(
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year > -3,
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 3,
        valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q)
    stocks = list(df_fundamentals.code)
    df = get_fundamentals(query(valuation.code).filter(valuation.code.in_(stocks)).order_by(valuation.market_cap.asc()))
    return list(df.code)
```

  * **功能说明** :

    * 筛选出PEG在一定范围内的股票，并根据市值进行排序，以找到具有较好成长性的低价股。

**5.3 获取昨日涨停股票**

```python
def get_high_limit(context):
    g.high_limit_list = []
    hold_list = list(context.portfolio.positions)
    if hold_list:
        df = get_price(hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1).iloc[:, 0, :]
        g.high_limit_list = list(df[df['close'] == df['high_limit']].index)
```

  * **功能说明** :

    * 获取昨日涨停的股票列表，以便在后续交易中进行特殊处理。

**5.4 检查涨停股票**

```python
def check_high_limit(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info("[%s]涨停打开，卖出" % stock)
                order_target(stock, 0)
            else:
                log.info("[%s]涨停
，继续持有" % stock)
```

  * **功能说明** :

    * 在日终检查涨停股票是否继续涨停，如果未继续涨停，则卖出该股票，反之则继续持有。

**5.5 全面过滤股票**

```python
def filter_all_stocks(context, stock_list):
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (
            stock.startswith(('68', '4', '8')) or
            curr_data[stock].paused or
            curr_data[stock].is_st or
            'ST' in curr_data[stock].name or
            '*' in curr_data[stock].name or
            '退' in curr_data[stock].name or
            curr_data[stock].last_price == curr_data[stock].high_limit or
            curr_data[stock].last_price == curr_data[stock].low_limit
    )]
```

  * **功能说明** :

    * 对股票列表进行全面的过滤，剔除科创板、北交所、ST股、退市股、涨跌停板股票等不符合标准的股票。

**5.6 过滤高价股**

```python
def filter_highprice_stock(context, stock_list):
    df = history(1, unit='1m', field='close', security_list=stock_list)
    price_list = df.values[0].copy()
    price_list.sort()
    price = price_list[int(0.75 * len(df.T))]
    return [stock for stock in stock_list if df[stock][-1] < price]
```

  * **功能说明** :

    * 通过筛选价格较低的股票，避免买入价格过高的股票，以降低投资风险。



### 总结

**稳健多因子筛选交易策略** 是一种综合考虑多个基本面因子的量化交易策略，通过股息率、PEG、股价等多维度筛选股票，建立一个稳健的股票投资组合，并通过定期的调仓和特殊处理（如涨停股）的方式进行动态调整，以期在保持较低风险的同时实现稳健的收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
