# 12、因子筛选与动量跟踪策略

# 策略概述

该策略是一个基于多因子筛选和动量跟踪的量化交易策略。策略通过筛选股票池中的优质股票并结合涨停情况进行持仓调整，力求在保持收益的同时控制风险。策略的核心在于通过因子筛选、动量分析及涨停过滤来进行股票筛选和仓位调整，最终提高投资组合的稳定性和收益率。

# 策略优化与详细代码说明

## 1. 初始化函数

**函数名：initialize**

```python
def initialize(context):
    # 设定基准
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 避免使用未来数据
    set_option("avoid_future_data", True)
    # 设置固定滑点
    set_slippage(FixedSlippage(0))
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    # 过滤低于错误级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10
    g.limit_up_list = []
    g.hold_list = []
    # 设置交易时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

**说明** ：

  * 初始化函数设置了策略的基准、滑点、交易成本等基本参数，并初始化了股票池及持仓列表。

  * 通过run_daily和run_weekly函数设置了策略的运行时间点，包括每日的股票池准备、每周的持仓调整及每日涨停检查。

## 2. 选股模块

**函数名：get_factor_filter_list**

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame({'code': stock_list, 'score': score_list}).dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    filter_list = list(df['code'])[int(p1*len(df)):int(p2*len(df))]
    return filter_list
```

**说明** ：

  * 该函数根据指定的因子和排序方式筛选股票，并返回排序后的股票列表，用于后续的投资组合构建。

**函数名：get_stock_list**

```python
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 用因子获取昨日收盘价并筛选
    price_list1 = get_factor_filter_list(context, initial_list, 'price_no_fq', True, 0, 0.1)
    # 通过流通市值和每股收益进一步筛选
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(price_list1)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    df = df[df['eps'] > 0]
    final_list = list(df.code)[:15]
    return final_list
```

**说明** ：

  * get_stock_list 函数通过一系列过滤器筛选出一组优质股票，并根据流通市值和每股收益排序，最终生成一个待投资的股票列表。

## 3. 持仓管理

**函数名：prepare_stock_list**

```python
def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = df[df['close'] == df['high_limit']]['code'].tolist()
    else:
        g.high_limit_list = []
```

**说明** ：

  * 该函数在每日开盘前准备股票池，并记录当前持有的股票以及涨停股票列表，为后续的持仓调整做准备。

**函数名：weekly_adjustment**

```python
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    target_list = target_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
            log.info("卖出[%s]" % stock)
            close_position(context.portfolio.positions[stock])
        else:
            log.info("已持有[%s]" % stock)
    position_count = len(context.portfolio.positions)
    target_num = len(target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == target_num:
                        break
```

**说明** ：

  * 每周调整持仓，根据新选出的股票列表进行调仓，卖出不符合条件的股票，并买入新的目标股票。

## 4. 涨停检查

**函数名：check_limit_up**

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                log.info("[%s]涨停打开，卖出" % stock)
                close_position(context.portfolio.positions[stock])
            else:
                log.info("[%s]涨停，继续持有" % stock)
```

**说明** ：

  * 每日尾盘检查持仓中的涨停股票，若涨停被打开则提前卖出，否则继续持有。

## 5. 交易模块

**自定义下单、开仓、平仓**

```python
def order_target_value_(security, value):
	if value == 0:
		log.debug("Selling out %s" % (security))
	else:
		log.debug("Order %s to value %f" % (security, value))
	return order_target_value(security, value)
def open_position(security, value):
	order = order_target_value_(security, value)
	return order is not None and order.filled > 0
def close_position(position):
	security = position.security
	order = order_target_value_(security, 0)
	return order is not None and order.status == OrderStatus.held and order.filled == order.amount
```

**说明** ：

  * 这些函数封装了下单、开仓和平仓逻辑，确保交易操作的可控性和稳定性。

## 6. 每日持仓信息打印

**函数名：print_position_info**

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
        print(f'代码: {securities}\n成本价: {cost:.2f}\n现价: {price}\n收益率: {ret:.2f}%\n持仓(股): {amount}\n市值: {value:.2f}\n{"—"*50}')
    print(f'{"—"*50}分割线{"—"*50}')
```

**说明** ：

  * 每日收盘后，打印当天的持仓信息和交易记录，便于后续复盘分析。

### 策略适用场景

“因子筛选与动量跟踪策略”适用于希望通过因子筛选获取高质量标的，并结合动量和市场信号进行持仓管理的投资者。该策略适合波动性较高的市场环境，能够有效地在市场中寻找优质股票并进行动态调整。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
