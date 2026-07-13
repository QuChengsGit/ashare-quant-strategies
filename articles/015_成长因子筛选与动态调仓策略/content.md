# 15、成长因子筛选与动态调仓策略

# 策略概述

该策略名为“成长因子筛选与动态调仓策略”，通过对上市公司的成长性进行评分，筛选出优质股票，持仓周期为一周。策略主要采用三个成长因子：营业收入增长率、利润总额增长率、五年盈利增长率，分别赋予不同权重进行打分，每周一调整持仓。该策略兼顾了成长性与市值平衡，以期获得较高的年化收益率。

# 策略优化与详细代码说明

## 1. 初始化函数

**函数名：initialize**

```python
def initialize(context):
    # 系统参数设置
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')
    # 策略参数设置
    g.stock_num = 5  # 持仓数
    g.no_trading_today_signal = False
    g.hold_list = []  # 当前持仓列表
    # 调度任务
    run_weekly(my_trade, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(close_account, '14:30')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

**说明** ：

  * 初始化函数设置了基准、交易参数（如滑点、交易成本）等基本系统参数。

  * 策略每周一调整持仓，每日检查是否需要清仓。

## 2. 选股模块

**函数名：get_stock_list**

```python
def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    factor_values = get_factor_values(initial_list, [
        'operating_revenue_growth_rate',  # 营业收入增长率
        'total_profit_growth_rate',       # 利润总额增长率
        'earnings_growth',                # 五年盈利增长率
    ], end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list)
    df['operating_revenue_growth_rate'] = list(factor_values['operating_revenue_growth_rate'].T.iloc[:, 0])
    df['total_profit_growth_rate'] = list(factor_values['total_profit_growth_rate'].T.iloc[:, 0])
    df['earnings_growth'] = list(factor_values['earnings_growth'].T.iloc[:, 0])
    df['total_score'] = (0.2 * df['operating_revenue_growth_rate'] +
                         0.4 * df['total_profit_growth_rate'] +
                         0.4 * df['earnings_growth'])
    df = df.sort_values(by=['total_score'], ascending=False)
    complex_growth_list = list(df.index)[:int(0.1 * len(df.index))]
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(complex_growth_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    df = df[df['eps'] > 0]
    return list(df.code)
```

**说明** ：

  * 通过三个成长因子进行打分，筛选出前10%的成长性较好的股票，再通过市值和EPS进行进一步筛选。

## 3. 调仓函数

**函数名：my_trade**

```python
def my_trade(context):
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')
    g.hold_list = list(context.portfolio.positions.keys())
    if g.no_trading_today_signal:
        return
    check_out_list = get_stock_list(context)
    check_out_list = filter_limitup_stock(context, check_out_list)
    check_out_list = filter_limitdown_stock(context, check_out_list)
    check_out_list = filter_paused_stock(check_out_list)
    check_out_list = check_out_list[:g.stock_num]
    adjust_position(context, check_out_list)
```

**说明** ：

  * 每周一进行调仓操作，先根据选股模块筛选出的股票列表，再根据涨停、跌停、停牌等因素进行二次过滤，最终调整持仓。

**函数名：adjust_position**

```python
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            log.info("[%s]不在应买入列表中" % stock)
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("[%s]已经持有无需重复买入" % stock)
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        break
```

**说明** ：

  * adjust_position函数负责执行调仓操作，卖出不在买入列表中的股票，买入新的目标股票。

## 4. 过滤器函数

**过滤器函数：**

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (current_data[stock].is_st or 'ST' in current_data[stock].name or '*' in current_data[stock].name or '退' in current_data[stock].name)]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] > current_data[stock].low_limit]
def filter_kcb_stock(context, stock_list):
    return [stock for stock in stock_list if stock[:3] != '688']
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [stock for stock in stock_list if yesterday - get_security_info(stock).start_date > datetime.timedelta(days=250)]
```

**说明** ：

  * 这些函数分别实现了停牌、ST股票、涨停、跌停、科创板、新股等过滤条件，确保最终选股结果符合策略要求。

## 5. 辅助函数

**函数名：today_is_between**

```python
def today_is_between(context, start_date, end_date):
    today = context.current_dt.strftime('%m-%d')
    return start_date <= today <= end_date
```

**说明** ：

  * 用于判断当前日期是否在特定的日期区间内，例如账户资金再平衡的时间段。

### 策略适用场景

该策略适用于成长型投资者，专注于选取成长性较高的个股，并通过定期调仓实现较高的收益率。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
