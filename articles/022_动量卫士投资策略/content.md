# 22、动量卫士投资策略

**概述**

动量卫士投资策略是一款综合动量投资与动态风险控制的量化交易策略。该策略利用股票的动量因子、市场趋势分析及风险控制机制，旨在通过优化资产配置，提升投资回报，并在复杂的市场环境中保持稳健的表现。



### 1. 初始化设置

```python
def initialize(context):
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_benchmark('000905.XSHG')
    set_slippage(PriceRelatedSlippage(0.000))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.0001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    g.stock_num = 10
    g.buylist = []
    g.new_high_value = context.portfolio.starting_cash
    g.maxdown = 0
    g.new_high_value = 0
    run_daily(get_high_limit_stocks, time='9:05', reference_security='000300.XSHG')
    run_monthly(select_stocks_and_buy, 1, time='9:30')
    run_daily(sell_stocks_opened_from_up_limit, time='14:00')
    run_daily(sell_hi_vol_stocks_at_dayend_and_buy_again, time='14:30')
    run_monthly(analyze_stocks_held, 1, time='15:01')
```

**功能说明** ：

  * 设置日志级别，确保订单相关的错误信息被记录。

  * 配置使用真实价格进行交易，并设定基准为中证500指数。

  * 设置滑点和交易成本，用于模拟实际交易环境。

  * 初始化全局变量，包括持仓股票数量、股票池、新资金高点和最大回撤值。

  * 定时任务安排：每日检查涨停股，每月选择并购买股票，每日处理涨停开盘的股票，尾盘处理高成交量股票，并每月分析持有股票的基本面数据。



### 2. 股票筛选与购买

```python
def select_stocks_and_buy(context):
    select_stocks(context)
    choice = g.buylist
    buy_stocks(context, g.buylist)
def select_stocks(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)
    q = query(valuation.code,
                valuation.pe_ratio / indicator.inc_net_profit_year_on_year,
                indicator.roe / valuation.pb_ratio,
                indicator.roe).filter(
                    valuation.pe_ratio / indicator.inc_net_profit_year_on_year > -1,
                    valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 3,
                    valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q, date=None)
    stocks = list(df_fundamentals.code)
    q = query(valuation.code, valuation.market_cap).filter(
        valuation.code.in_(stocks),
        valuation.market_cap <= 100).order_by(valuation.market_cap.asc())
    df = get_fundamentals(q, date=None)
    choice = list(df.code)
    choice = filter_st_stock(choice)
    choice = filter_paused_stock(choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    choice = choice[:g.stock_num * 2]
    g.buylist = choice
def buy_stocks(context, choice):
    position_count = len(context.portfolio.positions)
    if g.stock_num <= position_count:
        return
    buylist = choice
    psize = context.portfolio.available_cash / (g.stock_num - position_count)
    for s in buylist:
        if s not in context.portfolio.positions:
            log.info('buy', s)
            order_value(s, psize)
            if len(context.portfolio.positions) == g.stock_num:
                break
```

**功能说明** ：

  * select_stocks_and_buy：调用 select_stocks 筛选股票并执行购买操作。

  * select_stocks：从所有股票中筛选符合条件的股票，包括高股息股票、基本面良好且市值小于100亿的股票，并进行进一步过滤。

  * buy_stocks：根据剩余现金分配购买股票，确保总持仓不超过预设数量。



### 3. 股票出售

```python
def sell_stocks(context, sell_list):
    current_data = get_current_data()
    if len(sell_list) > 0:
        for security in sell_list:
            cprice = current_data[security].last_price
            boughtcost = context.portfolio.positions[security].avg_cost
            if context.portfolio.positions[security].avg_cost == 0:
                log.error("Sell %s " % (current_data[security].name), "avg_cost is 0")
                profit = 0
            else:
                profit = (cprice - boughtcost) / boughtcost * 100
            log.info("Sell %s " % (current_data[security].name), "profit: %.1f%%" % profit)
            limit_price = max(cprice * 0.95, current_data[security].low_limit)
            order_target_value(security, 0, LimitOrderStyle(limit_price))
def sell_stocks_opened_from_up_limit(context):
    cdata = get_current_data()
    sell_list = []
    if len(g.high_limit_list) > 0:
        for stock in g.high_limit_list:
            if cdata[stock].last_price < cdata[stock].high_limit:
                log.info("[%s]涨停打开，卖出" % cdata[stock].name)
                sell_list.append(stock)
    if sell_list:
        sell_stocks(context, sell_list)
def sell_hi_vol_stocks_at_dayend_and_buy_again(context):
    btlist = context.portfolio.positions
    cdata = get_current_data()
    sell_list = []
    for stock in btlist:
        if (cdata[stock].last_price == cdata[stock].high_limit):
            continue
        stock_now_vol = now_vol(context, stock)
        stock_ma10_vol = ma_vol(context, stock, 10)
        if (stock_now_vol > stock_ma10_vol * 3):
            log.info("[%s]放量未涨停，卖出" % cdata[stock].name)
            sell_list.append(stock)
    if sell_list:
        sell_stocks(context, sell_list)
    buy_stocks(context, g.buylist)
```

**功能说明** ：

  * sell_stocks：根据当前价格和持仓成本计算利润并执行卖出操作。设置限制价格以减少滑点。

  * sell_stocks_opened_from_up_limit：卖出昨日涨停但当日未再涨停的股票。

  * sell_hi_vol_stocks_at_dayend_and_buy_again：尾盘检查高成交量但未涨停的股票，卖出这些股票，并用剩余资金购买新的股票。



### 4. 股票池和数据分析

```python
def analyze_stocks_held(context):
    current_data = get_current_data()
    hold_stocks = context.portfolio.positions.keys()
    for s in hold_stocks:
        q = query(valuation.code, valuation.market_cap, valuation.pe_ratio, indicator.inc_net_profit_year_on_year).filter(valuation.code == s)
        df = get_fundamentals(q)
        log.info(s, current_data[s].name, '市盈率', df['pe_ratio'][0])
        log.info(s, current_data[s].name, '净利润同比增长率', df['inc_net_profit_year_on_year'][0])
    log.info('一天结束')
def after_trading_end(context):
    g.total_value = context.portfolio.total_value
    if g.total_value > g.new_high_value:
        g.new_high_value = g.total_value
        g.maxdown = 0
    else:
        max_down = (g.new_high_value - g.total_value) / g.new_high_value * 100
        g.maxdown = max_down if max_down > g.maxdown else g.maxdown
    record(maxdown=g.maxdown)
```

**功能说明** ：

  * analyze_stocks_held：分析持有股票的基本面数据，并记录市盈率和净利润同比增长率。

  * after_trading_end：计算并记录策略的总资金和最大回撤值，用于动态调整风险控制。



### 5. 股票过滤函数

```python
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] == '4' or stock[0] == '8' or stock[:2] == '68')]
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list
            if not current_data[stock].is_st
            and 'ST' not in current_data[stock].name
            and '*' not in current_data[stock
].name]
def filter_limitup_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if current_data[stock].last_price < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if current_data[stock].last_price > current_data[stock].low_limit]
def filter_highprice_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if current_data[stock].last_price <= 50]
def now_vol(context, stock):
    return history(1, '1d', 'volume', [stock]).iloc[0].values[0]
def ma_vol(context, stock, days):
    return history(days, '1d', 'volume', [stock]).mean()
```

**功能说明** ：

  * 股票过滤函数用于筛选合适的股票，包括过滤ST股票、暂停股票、涨停和跌停股票等。

  * now_vol 和 ma_vol 用于计算当前和历史成交量，用于判断成交量的异常情况。



### 总结

动量卫士投资策略结合动量投资与动态风险控制，具有自动筛选、购买和卖出股票的能力，通过持续优化投资组合，最大化投资回报，并在动态市场环境中保持稳健的表现。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
