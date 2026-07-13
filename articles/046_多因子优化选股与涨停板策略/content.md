# 46、多因子优化选股与涨停板策略

# 1. 策略概述

该策略主要结合多因子选股和涨停板操作策略，旨在通过筛选优质股票进行投资，并在每日和每周定期调仓中动态调整持仓。策略通过财务因子过滤股票，并根据市值、涨停、停牌等规则对股票进行进一步筛选，最终确定持仓股票池。此外，策略设置了涨停板股票的特殊处理方式，避免过早卖出潜力股。

# 2. 策略各部分功能代码详细技术文档说明

## 2.1 策略初始化 (initialize)

在策略初始化时，设置了基准、滑点、交易成本等基本参数。全局变量（如最大持仓数、限制交易天数等）被初始化，以便在后续操作中使用。

```python
def initialize(context):
    # 设置基准为中证500指数
    set_benchmark('000905.XSHG')
    # 启用真实价格交易模式，避免未来数据
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    # 设置滑点为0，交易成本为0.03%
    set_slippage(FixedSlippage(0))
    set_option('order_volume_ratio', 0.1)
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 设置日志级别为只显示error及以上级别日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10  # 最大持仓数量
    g.limit_days = 20  # 股票交易间隔限制
    g.high_limit_list = []  # 昨日涨停股列表
    g.hold_list = []  # 当前持仓列表
    g.history_hold_list = []  # 历史持仓记录
    g.not_buy_again_list = []  # 限制买入列表
    # 设置交易时间和频率
    run_daily(prepare_stock_list, time='9:00')
    run_weekly(weekly_adjustment, weekday=1, time='09:40')
    run_daily(check_limit_up, time='14:00')
    run_daily(print_position_info, time='15:30')
```

## 2.2 股票因子筛选与选股模块 (get_factor_filter_list, get_stock_list)

通过获取特定因子值并进行排序，从股票池中筛选出符合条件的股票。因子包括长期毛利率增长、每股净资产、非线性市值等，并最终返回三者并集后的股票列表。

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame({'code': stock_list, 'score': score_list}).dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    return list(df.code)[int(p1*len(df)):int(p2*len(df))]
def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    initial_list_1 = filter_new_stock(context, initial_list, 250)
    # 筛选长期毛利率增长最小的前10%股票
    test_list = get_factor_filter_list(context, initial_list_1, 'DEGM_8y', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(test_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    roa_list = list(df[df['eps']>0].code)[:5]
    # 筛选每股净资产最小的前10%股票
    test_list = get_factor_filter_list(context, initial_list_1, 'net_asset_per_share', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(test_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    reps_list = list(df[df['eps']>0].code)[:5]
    # 筛选非线性市值最小的前10%股票
    initial_list_2 = filter_new_stock(context, initial_list, 125)
    test_list = get_factor_filter_list(context, initial_list_2, 'non_linear_size', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(test_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    nls_list = list(df[df['eps']>0].code)[:5]
    # 并集去重后，返回按流通市值排序的最终列表
    union_list = list(set(roa_list).union(set(reps_list)).union(set(nls_list)))
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(union_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    return list(df.code)
```

## 2.3 调仓与买卖操作模块 (weekly_adjustment, open_position, close_position)

通过周调仓操作，策略根据选股列表中的股票进行买卖操作。同时，平仓策略会检查股票是否仍在持仓列表中，若不再持仓或未涨停，则执行平仓操作。

```python
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in target_list if stock not in black_list]
    target_list = target_list[:min(g.stock_num, len(target_list))]
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持有[%s]" % (stock))
    position_count = len(context.portfolio.positions)
    if len(target_list) > position_count:
        value = context.portfolio.cash / (len(target_list) - position_count)
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == len(target_list):
                        break
def open_position(security, value):
    order = order_target_value_(security, value)
    if order and order.filled > 0:
        return True
    return False
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    if order and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False
```

## 2.4 涨停板处理模块 (check_limit_up)

策略中特别处理昨日涨停的股票，检查当日是否继续涨停。如果涨停打开，则卖出该股票，否则继续持有。

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                log.info("[%s]涨停打开，卖出" % (stock))
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % (stock))
```

## 2.5 辅助与日志模块 (filter_paused_stock, filter_st_stock, print_position_info)

辅助函数用于对股票池进行进一步的过滤，如去除停牌股、ST股等。日志模块用于打印每个交易日的持仓信息，帮助投资者了解账户当前状况。

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get
_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
    for position in list(context.portfolio.positions.values()):
        print(f"代码:{position.security} 成本价:{format(position.avg_cost,'.2f')} 现价:{position.price} 收益率:{format(100*(position.price/position.avg_cost-1),'.2f')}% 持仓(股):{position.total_amount} 市值:{format(position.value,'.2f')}")
    print('——————分割线————')
```

# 3. 优化建议

  1. **参数优化** ：对筛选因子的阈值、持仓数量等参数进行回测优化，进一步提高策略表现。

  2. **动态调仓** ：根据市场变化动态调整调仓频率或持仓结构，以应对不同市场环境。

  3. **风险控制** ：引入最大回撤、止盈等风控策略，减少策略在极端市场环境下的损失。

通过以上的多因子选股和涨停板策略，能够在动态的市场中挑选出优质股票进行持有，并根据每日市场情况及时调整持仓，实现稳健的投资收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
