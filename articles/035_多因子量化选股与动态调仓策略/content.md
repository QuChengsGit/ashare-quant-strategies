# 35、多因子量化选股与动态调仓策略

# 1. 策略概述

该策略结合多因子选股模型与动态调仓机制，通过对财务因子、成长因子以及市场情绪因子的综合分析，筛选出具有较高投资价值的股票进行持仓。同时，策略动态监控持仓股票的涨停情况，并定期进行持仓调整，以实现收益最大化。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (initialize)

该模块用于初始化策略，设定基准指数、交易规则、滑点、交易成本，以及调度策略的运行时间。

```python
def initialize(context):
    # 设定基准指数为中证500
    set_benchmark('000905.XSHG')
    # 设定交易使用真实价格
    set_option('use_real_price', True)
    # 防止未来函数
    set_option("avoid_future_data", True)
    # 设置交易量限制
    set_option('order_volume_ratio', 1)
    # 设置滑点
    set_slippage(PriceRelatedSlippage(0.002), type='stock')
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=0.1), type='fund')
    # 过滤低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 9  # 最大持仓数
    g.limit_up_list = []  # 记录持仓中涨停的股票
    g.hold_list = []  # 当前持仓股票列表
    g.history_hold_list = []  # 过去持仓过的股票
    g.not_buy_again_list = []  # 不再买入的股票列表
    g.limit_days = 10  # 不再买入的时间段天数
    g.target_list = []  # 每日操作的目标股票列表
    # 设置交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

## 2.2 代码变更后初始化模块 (after_code_changed)

当代码变更后，重新初始化策略的运行调度。

```python
def after_code_changed(context):
    unschedule_all()
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

## 2.3 因子筛选模块 (get_factor_filter_list)

根据指定的因子，筛选出符合条件的股票列表。

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame(columns=['code', 'score'])
    df['code'] = stock_list
    df['score'] = score_list
    df = df.dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    filter_list = list(df.code)[int(p1 * len(stock_list)):int(p2 * len(stock_list))]
    return filter_list
```

## 2.4 股票筛选模块 (get_stock_list)

结合多因子模型筛选出目标股票列表，包括营业收入增长率、利润总额增长率、PEG等因子。

```python
def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = list(set(get_all_securities().index) & set(get_hot_industry_stock(context)))
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    # 筛选财务增长因子股票
    sg_list = get_factor_filter_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    # 综合成长因子筛选
    factor_values = get_factor_values(initial_list, ['operating_revenue_growth_rate', 'total_profit_growth_rate', 'net_profit_growth_rate', 'earnings_growth'], end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
    df['operating_revenue_growth_rate'] = list(factor_values['operating_revenue_growth_rate'].T.iloc[:, 0])
    df['total_profit_growth_rate'] = list(factor_values['total_profit_growth_rate'].T.iloc[:, 0])
    df['net_profit_growth_rate'] = list(factor_values['net_profit_growth_rate'].T.iloc[:, 0])
    df['earnings_growth'] = list(factor_values['earnings_growth'].T.iloc[:, 0])
    df['total_score'] = 0.1 * df['operating_revenue_growth_rate'] + 0.35 * df['total_profit_growth_rate'] + 0.15 * df['net_profit_growth_rate'] + 0.4 * df['earnings_growth']
    df = df.sort_values(by=['total_score'], ascending=False)
    complex_growth_list = list(df.index)[:int(0.1 * len(list(df.index)))]
    # 筛选PEG因子股票
    peg_list = get_factor_filter_list(context, initial_list, 'PEG', True, 0, 0.2)
    turnover_list = get_factor_filter_list(context, peg_list, 'turnover_volatility', True, 0, 0.5)
    final_list = [sg_list, list(df.code), peg_list]
    return final_list
```

## 2.5 准备股票池模块 (prepare_stock_list)

获取每日的目标股票列表，同时根据历史持仓情况决定哪些股票短期内不再买入。

```python
def prepare_stock_list(context):
    yesterday = context.previous_date
    g.hold_list = [position.security for position in list(context.portfolio.positions.values())]
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        for stock in hold_list:
            temp_set.add(stock)
    g.not_buy_again_list = list(temp_set)
    if g.hold_list:
        df = get_price(g.hold_list, end_date=yesterday, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.high_limit_list = list(df.code)
    else:
        g.high_limit_list = []
```

## 2.6 持仓调整模块 (weekly_adjustment)

每周对持仓股票进行调整，根据最新的目标股票池进行买入和卖出操作。

```python
def weekly_adjustment(context):
    all_list = get_stock_list(context)
    sg_list = all_list[0][:5]
    ms_list = all_list[1][:5]
    peg_list = all_list[2][:5]
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(union_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    g.target_list = list(df.code)
    g.target_list = filter_paused_stock(g.target_list)
    g.target_list = filter_limitup_stock(context, g.target_list)
    g.target_list = filter_limitdown_stock(context, g.target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    g.target_list = [stock for stock in g.target_list if stock not in black_list]
    g.target_list = g.target_list[:min(g.stock_num, len(g.target_list))]
    for stock in g.hold_list:
        if stock not in g.target_list and stock not in g.high_limit_list:
            position = context.portfolio.positions[stock]
            close_position(position)
    adjust_position(context, g.target_list, g.stock_num)
```

## 2.7 涨停股票检查模块 (check_limit_up)

每天检查持仓中的涨停股票，如尾盘未封涨停，则提前卖出。

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit
_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                position = context.portfolio.positions[stock]
                close_position(position)
```

## 2.8 打印持仓信息模块 (print_position_info)

每日打印当前持仓信息和交易记录。

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
        print(f'代码:{securities}')
        print(f'成本价:{format(cost, ".2f")}')
        print(f'现价:{price}')
        print(f'收益率:{format(ret, ".2f")}%')
        print(f'持仓(股):{amount}')
        print(f'市值:{format(value, ".2f")}')
        print('———————————————————————————————————')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
```

## 2.9 辅助函数

包括自定义下单、开仓、平仓和调仓等操作。

```python
def open_position(security, value):
    order = order_target_value(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    security = position.security
    order = order_target_value(security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
def adjust_position(context, buy_stocks, stock_num):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
    if stock_num > len(context.portfolio.positions):
        value = context.portfolio.cash / (stock_num - len(context.portfolio.positions))
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        break
```

# 3. 策略优化建议

  1. **动态调整因子权重** ：可以根据市场环境的变化，动态调整各因子在综合评分中的权重，以提升策略适应性。

  2. **增加风险管理机制** ：引入止损、止盈等机制，以降低市场波动带来的风险。

  3. **多元化选股** ：可以考虑引入更多的选股因子，如估值因子、技术指标等，以提升策略的全面性。

通过本策略，投资者可以利用多因子分析和动态调仓机制，筛选并持有优质股票，减少持仓风险，获取稳定收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
