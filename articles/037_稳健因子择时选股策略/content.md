# 37、稳健因子择时选股策略

# 1. 策略概述

该策略结合了因子选股与技术指标择时机制，通过多因子筛选模型挑选潜力股，并结合市场的整体动向进行风控操作。策略每日运行，动态调整持仓，并在市场风控信号出现时进行止损操作。策略的目标是稳健增值，并在控制风险的前提下，获取相对市场的超额收益。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (initialize)

此模块用于初始化策略的各项参数，包括设置交易基准、交易成本、滑点、日志级别等。此外，该模块还调度了策略运行的具体时间。

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准为中证500
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 防未来函数
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志输出等级
    # 初始化全局变量
    g.stock_num = 10  # 最大持仓数量
    g.limit_days = 20  # 持有天数限制
    g.limit_up_list = []  # 涨停股列表
    g.hold_list = []  # 当前持仓列表
    g.history_hold_list = []  # 历史持仓列表
    g.not_buy_again_list = []  # 不再买入的股票列表
    # 调度交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_daily(daily_adjustment, time='9:40', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

## 2.2 因子选股模块 (get_factor_filter_list)

该模块基于指定的因子对股票池进行筛选，返回满足因子条件的股票列表。

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame({'code': stock_list, 'score': score_list}).dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    return list(df.code)[int(p1 * len(df)):int(p2 * len(df))]
```

## 2.3 选股逻辑模块 (get_stock_list)

该模块结合多个因子（如长期资产回报率、每股留存收益、非线性市值）对股票进行筛选，生成目标股票池。

```python
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_kcbj_stock(initial_list)  # 过滤科创板和北交所股票
    initial_list = filter_st_stock(initial_list)  # 过滤ST股票
    initial_list_1 = filter_new_stock(context, initial_list, 250)  # 过滤次新股
    # 长期资产回报率筛选
    roa_list = get_factor_filter_list(context, initial_list_1, 'roa_ttm_8y', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(roa_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    roa_list = list(df[df['eps'] > 0].code)[:5]
    # 每股留存收益筛选
    reps_list = get_factor_filter_list(context, initial_list_1, 'retained_earnings_per_share', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(reps_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    reps_list = list(df[df['eps'] > 0].code)[:5]
    # 非线性市值筛选
    initial_list_2 = filter_new_stock(context, initial_list, 125)
    nls_list = get_factor_filter_list(context, initial_list_2, 'non_linear_size', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(nls_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    nls_list = list(df[df['eps'] > 0].code)[:5]
    # 取并集去重
    union_list = list(set(roa_list).union(set(reps_list)).union(set(nls_list)))
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(union_list)).order_by(valuation.circulating_market_cap.asc())
    return list(get_fundamentals(q, date=yesterday).code)
```

## 2.4 持仓调整模块 (daily_adjustment)

该模块每日根据选股池和市场信号调整持仓。当市场出现风险信号时，策略执行止损操作，空仓观望。

```python
def daily_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    base = get_bars('000852.XSHG', 30, unit='1d',
                    fields=['date', 'open', 'close', 'high', 'low', 'volume', 'money'],
                    include_now=False, end_dt=None, df=True)
    base['EMA2'] = talib.EMA(base['close'], 2)
    base['EMA4'] = talib.EMA(base['close'], 4)
    base['dif'] = base['EMA2'] - base['EMA4']
    base['dea'] = talib.EMA(base['dif'], 4)
    base['signal'] = np.where(base['dif'] - base['dea'] < 0, 1, 0)
    today_sig = np.array(base['signal'])[-1]
    if today_sig > 0:
        for stock in g.hold_list:
            position = context.portfolio.positions[stock]
            close_position(position)
            log.info(f"风控触发，平仓卖出{stock}")
        return
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info(f"卖出[{stock}]")
            position = context.portfolio.positions[stock]
            close_position(position)
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

## 2.5 涨停检查模块 (check_limit_up)

该模块检查持仓中涨停的股票，如果涨停被打开则立即卖出，否则继续持有。

```python
def check_limit_up(context):
    if g.high_limit_list:
        now_time = context.current_dt
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                log.info(f"[{stock}]涨停打开，卖出")
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info(f"[{stock}]涨停，继续持有")
```

## 2.6 过滤与辅助模块

这些模块用于对股票池进行各种过滤操作，并封装了买入、卖出等操作。

```python
# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
# 过滤ST及其他具有退市标签的股票
def
 filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
# 过滤涨停股票
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < current_data[stock].high_limit]
# 过滤跌停股票
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] > current_data[stock].low_limit]
# 过滤科创板和北交所股票
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if stock[0] != '4' and stock[0] != '8' and stock[:2] != '68']
# 过滤次新股
def filter_new_stock(context, stock_list, d):
    yesterday = context.previous_date
    return [stock for stock in stock_list if not yesterday - get_security_info(stock).start_date < datetime.timedelta(days=d)]
# 自定义下单
def order_target_value_(security, value):
    if value == 0:
        log.debug(f"Selling out {security}")
    else:
        log.debug(f"Order {security} to value {value}")
    return order_target_value(security, value)
# 开仓
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
# 平仓
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
```

## 2.7 打印持仓信息模块 (print_position_info)

该模块用于每日收盘后打印当前持仓信息及交易记录。

```python
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print(f'成交记录：{_trade}')
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print(f'代码:{securities}\n成本价:{cost:.2f}\n现价:{price}\n收益率:{ret:.2f}%\n持仓(股):{amount}\n市值:{value:.2f}')
        print('———————————————————————————————————')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
```

# 3. 策略优化建议

  1. **调仓机制** ：结合市场的变化，可以考虑增加更多的因子，或使用机器学习算法来动态调整选股标准。

  2. **风险控制** ：在风控方面，除了当前的信号外，可以引入更多的市场情绪指标（如VIX指数）作为辅助信号。

  3. **持仓管理** ：对于持仓股票，可以设置更为灵活的止盈止损机制，如基于ATR（平均真实波动幅度）的动态止损。

通过这些模块的优化和调整，该策略在稳定性和抗风险能力方面均有较好的表现，适合于追求稳健收益的投资者使用。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
