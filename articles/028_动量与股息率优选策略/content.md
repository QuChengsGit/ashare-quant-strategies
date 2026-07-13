# 28、动量与股息率优选策略

### 策略简介

“动量与股息率优选策略”是一种结合了股息率筛选和动量策略的量化交易模型。该策略首先通过股息率、PEG、ROE等多重指标筛选出基本面较为优质的股票，并结合价格动量、成交量等技术指标，在特定的市场环境下动态调整股票持仓。策略的核心在于寻找并持有基本面和技术面同时优异的股票，同时通过风控手段避免亏损。

### 策略结构与功能

### 1. 初始化函数

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设定基准指数为中证500
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option('avoid_future_data', True)  # 防止未来数据泄露
    set_slippage(PriceRelatedSlippage(0.000))  # 设置理想情况下的滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.0001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志级别为error
    g.stock_num = 10  # 持仓股票数量
    g.buylist = []  # 买入列表
    # 定时任务设置
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 准备股票池
    run_monthly(my_Trader, 1, time='9:30')  # 执行交易策略
    run_daily(check_limit_up, time='14:00')  # 检查并处理昨日涨停股票
    run_daily(check_at_dayend, time='14:30')  # 尾盘检查与交易调整
```

  * **功能说明** :

    * 初始化策略的各项参数和设置，定时运行相关的交易和检查函数。

    * 使用多个函数模块化实现策略逻辑，提高代码的可读性和维护性。

### 2. 获取股息率并筛选股票

```python
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365)
    interval = 1000
    list_len = len(stock_list)
    # 查询分红数据
    q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb).filter(
        finance.STK_XR_XD.a_registration_date >= time0,
        finance.STK_XR_XD.a_registration_date <= time1,
        finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)]))
    df = finance.run_query(q)
    # 如果列表过长，拆分查询
    if list_len > interval:
        df_num = list_len // interval
        for i in range(df_num):
            q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb).filter(
                finance.STK_XR_XD.a_registration_date >= time0,
                finance.STK_XR_XD.a_registration_date <= time1,
                finance.STK_XR_XD.code.in_(stock_list[interval*(i+1):min(list_len, interval*(i+2))]))
            temp_df = finance.run_query(q)
            df = df.append(temp_df)
    dividend = df.fillna(0).set_index('code').groupby('code').sum()
    # 获取市值数据并计算股息率
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(dividend.index))
    cap = get_fundamentals(q, date=time1).set_index('code')
    DR = pd.concat([dividend, cap], axis=1)
    DR['dividend_ratio'] = (DR['bonus_amount_rmb']/10000) / DR['market_cap']
    DR = DR.sort_values(by=['dividend_ratio'], ascending=sort)
    final_list = list(DR.index)[int(p1*len(DR)):int(p2*len(DR))]
    return final_list
```

  * **功能说明** :

    * 筛选过去一年股息率最高的股票，并进行排序和截取，获取指定区间的股票列表用于后续的进一步筛选。

### 3. 交易逻辑函数

**3.1 股票筛选与交易**

```python
def my_Trader(context):
    stocks = get_all_securities('stock', context.previous_date).index.tolist()
    stocks = filter_kcbj_stock(stocks)  # 过滤科创板和北交所股票
    # 选取高股息率股票
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    # 选取基本面优质股票
    q = query(valuation.code, valuation.pe_ratio / indicator.inc_net_profit_year_on_year, indicator.roe / valuation.pb_ratio, indicator.roe).filter(
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year > -1,
        valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 3,
        valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q)
    stocks = list(df_fundamentals.code)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(stocks), valuation.market_cap <= 100).order_by(valuation.market_cap.asc())
    df = get_fundamentals(q)
    choice = filter_st_stock(list(df.code))
    choice = filter_paused_stock(choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    g.buylist = choice
    buystock(context, g.buylist)
```

  * **功能说明** :

    * 综合股息率、PEG、ROE等指标筛选出基本面和技术面均优异的股票。

    * 执行买入操作，将选定的股票加入持仓。

**3.2 买入逻辑**

```python
def buystock(context, choice):
    position_count = len(context.portfolio.positions)
    if g.stock_num <= position_count:
        return
    psize = context.portfolio.available_cash / (g.stock_num - position_count)
    for s in choice:
        if s not in context.portfolio.positions:
            log.info('买入', s, get_current_data()[s].name)
            order_value(s, psize)
            if len(context.portfolio.positions) == g.stock_num:
                break
```

  * **功能说明** :

    * 根据筛选结果逐步买入股票，直到持仓数量达到设定的最大值。

**3.3 卖出逻辑**

```python
def sellstock(context, sell_list):
    current_data = get_current_data()
    for security in sell_list:
        cprice = current_data[security].last_price
        boughtcost = context.portfolio.positions[security].acc_avg_cost
        profit = (cprice - boughtcost) / boughtcost * 100
        log.info("卖出 %s " % (current_data[security].name), "收益: %.1f%%" % profit)
        limit_price = max(cprice * 0.95, current_data[security].low_limit)
        order_target_value(security, 0, LimitOrderStyle(limit_price))
```

  * **功能说明** :

    * 根据策略卖出不符合条件的股票或达到止盈/止损条件的股票。

### 4. 风控模块

**4.1 处理昨日涨停股票**

```python
def check_limit_up(context):
    cdata = get_current_data()
    sell_list = []
    for stock in g.high_limit_list:
        if cdata[stock].last_price < cdata[stock].high_limit:
            log.info("[%s]涨停打开，卖出" % cdata[stock].name)
            sell_list.append(stock)
    if sell_list:
        sellstock(context, sell_list)
```

  * **功能说明** :

    * 检查并处理昨日涨停后今日未继续涨停的股票，防止股票的高位回落。

**4.2 尾盘检查与调整**

```python
def check_at_dayend(context):
    btlist = context.portfolio.positions
    cdata = get_current_data()
    VOLT, MAVOL5, MAVOL10 = VOL(btlist, check_date=context.current_dt, M1=5, M2=10, include_now=True)
    sell_list = []
    for stock in btlist:
        if cdata[stock].last_price != cdata[stock].high_limit and VOLT[stock] > MAVOL10[stock] * 3:
            log.info("[%s]放量未涨停，卖出" % cdata[stock].name)
            sell_list
.append(stock)
    sellstock(context, sell_list)
    buystock(context, g.buylist)
```

  * **功能说明** :

    * 在尾盘检查股票的成交量与价格变化，对于放量未涨停的股票进行卖出操作。

### 5. 辅助函数

**5.1 股票筛选**

```python
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] == '4' or stock[0] == '8' or stock[:2] == '68')]
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] > current_data[stock].low_limit]
def filter_highprice_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < 9]
```

  * **功能说明** :

    * 对股票列表进行多维度的过滤，排除不符合条件的股票。



### 总结

动量与股息率优选策略结合了股息率筛选和动量分析，既保证了股票的基本面稳健性，又通过动量指标捕捉了市场中的交易机会。策略通过严格的风控手段控制回撤和亏损，力求在波动的市场中取得稳定的收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
