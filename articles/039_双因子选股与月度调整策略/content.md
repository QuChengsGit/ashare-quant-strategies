# 39、双因子选股与月度调整策略

# 1. 策略概述

本策略基于双因子选股模型，通过对股票的自由现金流/市值和ROE（净资产收益率）两个因子进行分析，筛选出具有投资潜力的股票，并在每月进行持仓调整。策略还包含涨停板处理逻辑，对于昨日涨停但今天涨停被打开的股票进行及时卖出，以确保收益的实现和风险控制。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (initialize)

该模块用于设置策略的初始参数，包括交易基准、交易成本、日志级别等，并初始化全局变量，如持股数量、检查涨停天数等。还定义了策略运行的调度时间。

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准为中证500
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 启用防未来数据保护
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    # 初始化全局变量
    g.stock_num = 8  # 目标持股数
    g.limit_days = 20  # 检查过去20天内的涨停股票
    g.hold_list = []  # 当前持仓股票列表
    # 设置策略运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(monthly_adjustment, monthday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
```

## 2.2 选股模块 (get_stock_list)

该模块基于自由现金流/市值和ROE因子进行选股，首先对股票池进行过滤，如去除科创板和ST股票、去除次新股等，然后对自由现金流/市值、ROE等因子进行去极值化、中性化和标准化处理，最终根据综合得分排序，选出前10只股票作为目标股票池。

```python
def get_stock_list(context):
    yesterday = context.previous_date
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 过滤科创板、ST股票
    initial_list = filter_kcb_stock(initial_list)
    sample = filter_st_stock(initial_list)
    # 计算FCF/市值和ROE因子
    q = query(
        valuation.code,
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / 100000000,
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / (valuation.market_cap * 100000000),
        indicator.roe,
        indicator.net_profit_margin,
        indicator.inc_net_profit_year_on_year,
        valuation.circulating_market_cap
    ).filter(
        valuation.code.in_(sample),
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / (valuation.market_cap * 100000000) > 0.02,
        indicator.adjusted_profit > 0,
        indicator.roe > 3,
        indicator.net_profit_margin > 10,
        indicator.inc_net_profit_to_shareholders_year_on_year > 5
    ).order_by(
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / (valuation.market_cap * 100000000).desc()
    )
    df = get_fundamentals(q)
    df.columns = ['code', '自由现金流（亿元）', 'FCF/市值(排序列)', 'roe', '净利率', '归母净利润YOY', '流通市值']
    df.index = df['code']
    df.drop(columns=['code'], inplace=True)
    # 因子处理：去极值、中性化、标准化
    factors_list = ['FCF/市值(排序列)', 'roe']
    df['score'] = 0
    for factor in factors_list:
        df[factor] = winsorize(df[factor], qrange=[0.05, 0.93])
        df[factor] = neutralize(df[factor], how=['jq_l1', 'market_cap'])
        df[factor] = standardlize(df[factor])
        df['score'] += df[factor]
    # 根据得分排序，选出前10个股票
    df_sorted = df.sort_values('score', ascending=False).iloc[:10]
    return df_sorted.index.tolist()
```

## 2.3 股票池准备模块 (prepare_stock_list)

该模块每日更新持仓股票列表，并获取前一日的涨停股票列表，作为后续卖出判断的依据。

```python
def prepare_stock_list(context):
    g.hold_list = list(context.portfolio.positions)  # 更新持仓列表
    # 获取持仓的昨日涨停股票列表
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close == high_limit and paused == 0')['code'].tolist()
```

## 2.4 月度调整模块 (monthly_adjustment)

每月根据选股结果调整持仓，卖出不符合条件的股票并买入新选出的目标股票。

```python
def monthly_adjustment(context):
    target_list = get_stock_list(context)  # 获取目标股票列表
    target_list = filter_paused_stock(target_list)
    target_list = filter_limit_stock(context, target_list)
    # 卖出不在目标列表中的股票
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
            log.info(f"卖出[{stock}]")
            position = context.portfolio.positions[stock]
            close_position(position)
    # 买入新的目标股票
    position_count = len(context.portfolio.positions)
    target_num = g.stock_num
    if target_num > position_count:
        value = context.portfolio.available_cash / (target_num - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) >= g.stock_num:
                        break
```

## 2.5 涨停处理模块 (check_limit_up)

该模块在每日14:00检查前一日涨停的股票，若今日涨停被打开，则立即卖出该股票。

```python
def check_limit_up(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info(f"[{stock}]涨停打开，卖出")
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info(f"[{stock}]涨停，继续持有")
```

## 2.6 股票过滤模块

包含多个股票过滤函数，如过滤停牌股票、过滤ST股票、过滤涨停板股票等，确保选股结果符合策略要求。

```python
# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
# 过滤ST及其他具有退市标签的股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
            current_data[stock].is_st or
            'ST' in current_data[stock].name or
            '*' in current_data[stock].name or
            '退' in current_data[stock].name)]
# 过滤涨停和跌停的股票
def filter_limit_stock(context, stock_list):
    current_data = get_current_data()
    holdings = list(context.portfolio.positions)
    return [stock for stock in stock_list if (stock in holdings) or
            current_data[stock].low_limit < current_data[stock].last_price < current_data[stock].high_limit]
# 过滤科创板股票
def filter_kcb_stock(stock_list):
    return [stock for stock in stock_list if not stock.startswith('68')]
```

## 2.7 交易模块

包含开仓、平仓和自定义下单的函数，用于执行具体的交易操作。

```python
# 自定义下单函数
def order_target_value_(security, value):
    if value == 0:
        log.debug(f"Selling out {security}")
    else:
        log.debug(f"Order {security} to value {value:.2f}")
    return order_target_value(security, value)
# 开仓函数
def open_position(security, value):
    _order = order_target_value_(security, value)
    if _order is not None and _order.filled > 0:
        return True
    return False
# 平仓
函数
def close_position(position):
    security = position.security
    _order = order_target_value_(security, 0)
    if _order is not None:
        if _order.status == OrderStatus.held and _order.filled == _order.amount:
            return True
    return False
```

# 3. 策略优化建议

  1. **因子增强** ：可以引入更多的因子如盈利能力、成长性因子，以提高策略的全面性和稳定性。

  2. **多频率调整** ：可以根据市场波动情况，动态调整持仓周期，如加入周度或季度调整，灵活应对市场变化。

  3. **风险控制** ：引入止损机制、仓位控制等风控手段，进一步减少策略的最大回撤。

通过这些优化，该策略可以更好地捕捉市场中的潜在机会，同时降低交易过程中的风险，提升整体收益的稳定性。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
