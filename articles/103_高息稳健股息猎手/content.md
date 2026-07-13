# 103、高息稳健股息猎手

### 策略概述

**高息稳健股息猎手** 策略是一个基于股息率和基本面分析的量化交易策略，主要用于股票市场的投资。策略的核心思想是通过筛选高股息率的股票，结合基本面数据和市场状态，构建一个稳健的投资组合。策略的目标是在保证收益的同时，降低投资风险，实现长期稳定的资产增值。

### 策略详细介绍

1\. 初始化设置

在策略的初始化阶段，进行了以下设置：

```python
def initialize(context):
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_benchmark('000905.XSHG')
    set_slippage(PriceRelatedSlippage(0.000))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    g.stock_num = 10
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(my_Trader, 1, time='9:30')
    run_daily(check_limit_up, time='14:00')
```

  * **日志级别** ：设置日志级别为error，减少不必要的日志输出。

  * **复权模式** ：开启动态复权模式，使用真实价格进行交易。

  * **基准设定** ：将中证500指数（000905.XSHG）设定为基准。

  * **滑点设置** ：设置滑点为理想情况，纯为了跑分好看，实际使用注释掉为好。

  * **手续费设置** ：设定股票交易的手续费和印花税。

  * **运行时间** ：每日9:05准备股票池，每月第一个交易日9:30进行交易，每日14:00检查涨停股票。

2\. 数据准备

2.1 股息率筛选

```python
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365)
    q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
    ).filter(
        finance.STK_XR_XD.a_registration_date >= time0,
        finance.STK_XR_XD.a_registration_date <= time1,
        finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)]))
    df = finance.run_query(q)
    if list_len > interval:
        df_num = list_len // interval
        for i in range(df_num):
            q = query(finance.STK_XR_XD.code, finance.STK_XR_XD.a_registration_date, finance.STK_XR_XD.bonus_amount_rmb
            ).filter(
                finance.STK_XR_XD.a_registration_date >= time0,
                finance.STK_XR_XD.a_registration_date <= time1,
                finance.STK_XR_XD.code.in_(stock_list[interval*(i+1):min(list_len,interval*(i+2))]))
            temp_df = finance.run_query(q)
            df = df.append(temp_df)
    dividend = df.fillna(0)
    dividend = dividend.set_index('code')
    dividend = dividend.groupby('code').sum()
    temp_list = list(dividend.index)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(temp_list))
    cap = get_fundamentals(q, date=time1)
    cap = cap.set_index('code')
    DR = pd.concat([dividend, cap], axis=1, sort=False)
    DR['dividend_ratio'] = (DR['bonus_amount_rmb']/10000) / DR['market_cap']
    DR = DR.sort_values(by=['dividend_ratio'], ascending=sort)
    final_list = list(DR.index)[int(p1*len(DR)):int(p2*len(DR))]
    return final_list
```

  * **股息率计算** ：根据最近一年的分红数据和当前总市值计算股息率，并筛选出股息率最高的股票。

  * **数据查询** ：通过finance.run_query获取分红数据和市值数据，并进行合并计算。

3\. 交易逻辑

3.1 交易执行

```python
def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    df = get_fundamentals(query(valuation.code).filter(valuation.code.in_(stocks)).order_by(valuation.market_cap.asc()))
    choice = list(df.code)
    choice = filter_st_stock(choice)
    choice = filter_paused_stock(choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    choice = choice[:g.stock_num]
    cdata = get_current_data()
    for s in context.portfolio.positions:
        if (s not in choice):
            log.info('Sell', s, cdata[s].name)
            order_target(s, 0)
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        psize = context.portfolio.available_cash/(g.stock_num - position_count)
        for s in choice:
            if s not in context.portfolio.positions:
                log.info('buy', s, cdata[s].name)
                order_value(s, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break
```

  * **股票筛选** ：从全市场中筛选出股息率最高的25%股票，并进行基本面和市场状态的过滤。

  * **买卖操作** ：卖出不在筛选列表中的股票，买入筛选列表中的股票，保持持仓数量为10只。

3.2 涨停检查

```python
def check_limit_up(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info("[%s]涨停打开，卖出" % stock)
                order_target(stock, 0)
            else:
                log.info("[%s]涨停，继续持有" % stock)
```

  * **涨停检查** ：每日14:00检查持仓中的涨停股票，如果涨停打开则卖出。

4\. 辅助函数

4.1 过滤函数

```python
def filter_kcbj_stock(stock_list):
    for stock in stock_list[:]:
        if stock[0] == '4' or stock[0] == '8' or stock[:2] == '68':
            stock_list.remove(stock)
    return stock_list
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list
            if not current_data[stock].is_st
            and 'ST' not in current_data[stock].name
            and '*' not in current_data[stock].name
            and '退' not in current_data[stock].name]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[stock][-1] < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[stock][-1] > current_data[stock].low_limit]
def filter_highprice_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[stock][-1] < 9]
```

  * **过滤科创北交股票** ：过滤科创板和北交所的股票。

  * **过滤停牌股票** ：过滤停牌的股票。

  * **过滤ST及其他具有退市标签的股票** ：过滤ST股票和具有退市标签的股票。

  * **过滤涨停的股票** ：过滤涨停的股票，但持仓中的股票除外。

  * **过滤跌停的股票** ：过滤跌停的股票，但持仓中的股票除外。

  * **过滤股价高于9元的股票** ：过滤股价高于9元的股票。

### 总结

**高息稳健股息猎手** 策略通过筛选高股息率的股票，结合基本面数据和市场状态，构建一个稳健的投资组合。策略的核心在于通过股息率筛选出具有稳定分红能力的股票，并在交易时进行多重过滤，确保投资组合的质量和稳定性。同时，策略通过定期检查涨停股票，及时调整持仓，进一步降低投资风险。总体而言，该策略适合追求稳健收益的投资者，能够在市场波动中保持资产的稳定增值。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
