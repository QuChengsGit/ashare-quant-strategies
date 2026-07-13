# 5、多因子择优选股策略

# 1. 策略概述

该策略基于多因子模型，通过技术指标和财务因子对股票进行筛选和排序，选出最优的股票组合进行投资。策略主要采用技术因子（如不复权价格）、财务质量因子（如成本费用利润率、存货周转率）来计算每只股票的得分，并在每周调整持仓，确保组合的优质性和稳定性。本文完整代码下载方式请见文末。

# 2. 策略逻辑

  1. **多因子选股** ：

     * 使用技术指标因子、质量类因子等多种因子计算每只股票的综合得分，并基于得分进行排序，选出得分最高的股票作为候选标的。

  2. **持仓调整** ：

     * 每周根据最新得分对持仓进行调整，卖出不再符合条件的股票，并买入新的高分股票。

  3. **风控措施** ：

     * 通过过滤涨停、跌停、ST、次新股、科创板股票等高风险股票，减少组合的不确定性和波动风险。

# 3. 策略代码详细说明

## 3.1 初始化函数 (initialize)

```python
def initialize(context):
    # 设置策略的基准指数
    set_benchmark('399303.XSHE')  # 选取中证1000指数作为基准
    # 使用真实价格进行交易
    set_option('use_real_price', True)
    # 防止未来数据干扰
    set_option("avoid_future_data", True)
    # 设置固定滑点为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 过滤日志，仅保留error级别以上的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10  # 最大持股数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票
    g.factor_list = [
        'price_no_fq',  # 技术指标因子：不复权价格
        'total_profit_to_cost_ratio',  # 质量类因子：成本费用利润率
        'inventory_turnover_rate'  # 质量类因子：存货周转率
    ]
    # 每日、每周的调度任务
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

**功能** ：初始化策略的基本配置，包括设定基准、滑点、交易成本及每日、每周的调度任务。

## 3.2 股票池准备与筛选 (prepare_stock_list)

```python
def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.yesterday_HL_list = list(df.code)
    else:
        g.yesterday_HL_list = []
```

**功能** ：获取当前持仓的股票，并记录其中昨日涨停的股票。

## 3.3 选股逻辑 (get_stock_list)

```python
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 获取因子值
    factor_values = get_factor_values(initial_list, g.factor_list, end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list, columns=g.factor_list)
    for factor in g.factor_list:
        df[factor] = factor_values[factor].T.iloc[:, 0]
    df = df.dropna()
    # 因子加权计算总得分
    coef_list = [-6.123e-05, -0.002579, -2.194e-06]
    df['total_score'] = sum(coef * df[factor] for coef, factor in zip(coef_list, g.factor_list))
    # 根据得分排序并筛选前10%的股票
    df = df.sort_values(by='total_score', ascending=False)
    top_stocks = df.index[:int(0.1 * len(df.index))]
    # 进一步筛选流通市值和盈利状况
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(top_stocks)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    final_list = df[df['eps'] > 0].code.tolist()
    return final_list
```

**功能** ：基于多因子模型对股票进行打分和排序，最终选出得分最高的股票。

## 3.4 持仓调整 (weekly_adjustment)

```python
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    # 限制持仓数量
    target_list = target_list[:min(g.stock_num, len(target_list))]
    # 调整持仓，卖出不在目标列表中的股票
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.yesterday_HL_list:
            log.info(f"卖出[{stock}]")
            close_position(context.portfolio.positions[stock])
    # 买入目标列表中的股票
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

**功能** ：每周进行持仓调整，卖出不符合条件的股票，买入新的高分股票。

## 3.5 涨停股监控 (check_limit_up)

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                log.info(f"[{stock}]涨停打开，卖出")
                close_position(context.portfolio.positions[stock])
            else:
                log.info(f"[{stock}]涨停，继续持有")
```

**功能** ：检查昨日涨停股票的当前状态，如果涨停板被打开则卖出，否则继续持有。

## 3.6 股票过滤函数

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not stock.startswith(('4', '8', '68'))]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
 or last_prices[stock][-1] > current_data[stock].low_limit]
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [stock for stock in stock_list if not yesterday - get_security_info(stock).start_date < datetime.timedelta(days=375)]
```

**功能** ：过滤掉停牌、ST、次新股和科创板股票，以及当日涨停或跌停的股票，减少组合的潜在风险。

## 3.7 交易模块

```python
def order_target_value_(security, value):
    if value == 0:
        log.debug(f"Selling out {security}")
    else:
        log.debug(f"Order {security} to value {value}")
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    if order is not None and order.filled > 0:
        return True
    return False
def close_position(position):
    order = order_target_value_(position.security, 0)
    if order is not None and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False
```

**功能** ：提供自定义的开仓、平仓和交易下单函数。

## 3.8 每日持仓信息打印 (print_position_info)

```python
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print(f'成交记录：{_trade}')
    for position in context.portfolio.positions.values():
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print(f'代码: {securities}')
        print(f'成本价: {cost:.2f}')
        print(f'现价: {price}')
        print(f'收益率: {ret:.2f}%')
        print(f'持仓(股): {amount}')
        print(f'市值: {value:.2f}')
        print('———————————————————————————————————')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
```

**功能** ：每日打印持仓信息和当日交易记录，方便跟踪和分析策略表现。

# 4. 策略总结

**“多因子择优选股策略”** 是一个基于多因子模型的量化策略，通过技术和财务因子的综合评分选出优质股票，并通过周度调整持仓来保持组合的高质量和稳定性。该策略能够在控制风险的同时，获取市场中的超额收益。

## 多因子择优选股策略完整代码

下载链接: <https://pan.baidu.com/s/1-j19r_B7tdtqXafLn6J-yA>

提取码: rmm7

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
