# 104、因子轮动稳健猎手

### 策略概述

**因子轮动稳健猎手** 策略是一个基于因子分析和市场择时的量化交易策略，主要用于股票市场的投资。策略的核心思想是通过筛选具有特定因子优势的股票，结合市场状态和基本面数据，构建一个稳健的投资组合。策略的目标是在保证收益的同时，降低投资风险，实现长期稳定的资产增值。

### 策略详细介绍

1\. 初始化设置

在策略的初始化阶段，进行了以下设置：

```python
def initialize(context):
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')
    g.stock_num = 10
    g.limit_up_list = []
    g.hold_list = []
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

  * **基准设定** ：将中证500指数（000905.XSHG）设定为基准。

  * **复权模式** ：开启动态复权模式，使用真实价格进行交易。

  * **防未来函数** ：打开防未来函数，避免使用未来数据。

  * **滑点设置** ：将滑点设置为0，确保交易价格为理想情况。

  * **手续费设置** ：设定股票交易的手续费和印花税。

  * **日志级别** ：过滤order中低于error级别的日志。

  * **运行时间** ：每日9:05准备股票池，每周一9:30进行交易，每日14:00检查涨停股票，每日15:10打印持仓信息。

2\. 数据准备

2.1 因子筛选

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame(columns=['code', 'score'])
    df['code'] = stock_list
    df['score'] = score_list
    df = df.dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    filter_list = list(df.code)[int(p1*len(df)):int(p2*len(df))]
    return filter_list
```

  * **因子筛选** ：根据特定因子（如价格、市值等）对股票进行评分，并筛选出评分最高的股票。

2.2 股票池构建

```python
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    price_list1 = get_factor_filter_list(context, initial_list, 'price_no_fq', True, 0, 0.1)
    df = get_price(initial_list, start_date=yesterday, end_date=yesterday, fields=['close'], fq='pre', panel=False)
    df = df.sort_values(by='close', ascending=True)
    price_list2 = list(df.code)[int(0*len(df)):int(0.1*len(df))]
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(price_list1)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    df = df[df['eps'] > 0]
    final_list = list(df.code)[:15]
    return final_list
```

  * **股票池构建** ：从全市场中筛选出价格较低的股票，并结合流通市值和每股收益（EPS）进行进一步筛选，构建最终的股票池。

2.3 准备股票池

```python
def prepare_stock_list(context):
    g.hold_list = []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    if g.hold_list != []:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.high_limit_list = list(df.code)
    else:
        g.high_limit_list = []
```

  * **准备股票池** ：获取已持有股票列表和昨日涨停股票列表，为后续交易做准备。

3\. 交易逻辑

3.1 每周调整持仓

```python
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    target_list = target_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持有[%s]" % (stock))
    position_count = len(context.portfolio.positions)
    target_num = len(target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == target_num:
                        break
```

  * **每周调整持仓** ：每周一9:30根据股票池进行调仓，卖出不在股票池中的股票，买入股票池中的股票，保持持仓数量为10只。

3.2 涨停检查

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list != []:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                log.info("[%s]涨停打开，卖出" % (stock))
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % (stock))
```

  * **涨停检查** ：每日14:00检查持仓中的涨停股票，如果涨停打开则卖出。

4\. 辅助函数

4.1 过滤函数

```python
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
def filter_kcbj_stock(stock_list):
    for stock in stock_list[:]:
        if stock[0] == '4' or stock[0] == '8' or stock[:2] == '68':
            stock_list.remove(stock)
    return stock_list
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [stock for stock in stock_list if not yesterday - get_security_info(stock).start_date < datetime.timedelta(days=250)]
```

  * **过滤停牌股票** ：过滤停牌的股票。

  * **过滤ST及其他具有退市标签的股票** ：过滤ST股票和具有退市标签的股票。

  * **过滤涨停的股票** ：过滤涨停的股票，但持仓中的股票除外。

  * **过滤跌停的股票** ：过滤跌停的股票，但持仓中的股票除外。

  * **过滤科创北交股票** ：过滤科创板和北交所的股票。

  * **过滤次新股** ：过滤上市不满250天的次新股。

4.2 交易模块

```python
def order_target_value_(security, value):
    if value == 0:
        log.debug("Selling out %s" % (security))
    else:
        log.debug("Order %s to value %f" % (security, value))
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    if order != None and order.filled > 0:
        return True
    return False
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    if order != None:
        if order.status == OrderStatus.held and order.filled == order.amount:
            return True
    return False
```

  * **自定义下单** ：自定义下单函数，用于开仓和平仓操作。

  * **开仓** ：根据指定金额开仓。

  * **平仓** ：将指定股票的持仓平仓。

4.3 打印持仓信息

```python
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print('代码:{}'.format(securities))
        print('成本价:{}'.format(format(cost, '.2f')))
        print('现价:{}'.format(price))
        print('收益率:{}%'.format(format(ret, '.2f')))
        print('持仓(股):{}'.format(amount))
        print('市值:{}'.format(format(value, '.2f')))
        print('————————')
    print('—————————分割线————————————')
```

  * **打印持仓信息** ：每日15:10打印当天的成交记录和持仓信息，包括代码、成本价、现价、收益率、持仓数量和市值。

### 总结

**因子轮动稳健猎手** 策略通过筛选具有特定因子优势的股票，结合市场状态和基本面数据，构建一个稳健的投资组合。策略的核心在于通过因子分析和市场择时，捕捉具有潜力的股票，并在交易时进行多重过滤，确保投资组合的质量和稳定性。同时，策略通过定期检查涨停股票，及时调整持仓，进一步降低投资风险。总体而言，该策略适合追求稳健收益的投资者，能够在市场波动中保持资产的稳定增值。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
