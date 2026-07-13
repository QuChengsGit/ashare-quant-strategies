# 69、多因子量化选股策略

### 策略介绍

**多因子量化选股策略** 是一种结合多因子分析和严格风控的主动选股策略。该策略利用多种财务指标和市场因素对股票进行筛选，构建投资组合，并通过动态调整持仓来优化收益。策略核心在于通过定期筛选优质股票并规避风险较高的标的，保持投资组合的稳健增长。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设定中证500指数为基准
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 避免未来数据影响
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    g.stock_num = 10  # 最大持仓数
    g.limit_up_list = []  # 记录持仓中涨停的股票
    g.hold_list = []  # 当前持仓的全部股票
    g.history_hold_list = []  # 过去一段时间内持仓过的股票
    g.not_buy_again_list = []  # 最近买过且涨停过的股票不再买入的名单
    g.limit_days = 20  # 不再买入的时间段天数
    g.target_list = []  # 开盘前预操作的股票池
    # 自定义因子及分位值，设定多因子筛选
    g.factor1, g.P1, g.sort1 = 'net_profit_growth_rate', 0.1, False
    g.factor2, g.P2, g.sort2 = 'EBIT', 0.4, True
    g.factor3, g.P3, g.sort3 = 'roe_ttm', 1, False  # roe_ttm作为备用因子
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 准备股票池
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一调仓
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 检查持仓中涨停股
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')  # 打印每日持仓信息
```

技术说明：

  * **滑点与交易成本** ：设定了固定的交易滑点和合理的交易成本，确保交易结果更接近真实市场。

  * **多因子筛选** ：通过多个财务因子（如净利润增长率、EBIT、ROE等）对股票进行多层次筛选。

2\. 选股模块

2-1 因子筛选函数

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame({'code': stock_list, 'score': score_list}).dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    return list(df.code)[:int(p * len(stock_list))]
```

2-2 选股函数

```python
def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    factor1_list = get_factor_filter_list(context, initial_list, g.factor1, g.sort1, g.P1)
    factor2_list = get_factor_filter_list(context, factor1_list, g.factor2, g.sort2, g.P2)
    factor3_list = get_factor_filter_list(context, factor2_list, g.factor3, g.sort3, g.P3)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(
        valuation.code.in_(factor3_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q).dropna()
    return list(df[df['eps'] > 0].code)
```

技术说明：

  * **因子筛选** ：根据自定义因子对股票池进行多次筛选，最终得到符合标准的股票列表。

  * **选股逻辑** ：优先选取在多因子评分中表现较好的股票，去除亏损公司，确保投资组合的质量。

3\. 调仓与风险控制

3-1 调仓与持仓管理

```python
def weekly_adjustment(context):
    g.target_list = get_stock_list(context)[:g.stock_num + 5]
    g.target_list = filter_paused_stock(g.target_list)
    g.target_list = filter_limitup_stock(context, g.target_list)
    g.target_list = filter_limitdown_stock(context, g.target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    g.target_list = [stock for stock in g.target_list if stock not in black_list]
    g.target_list = g.target_list[:min(g.stock_num, len(g.target_list))]
    for stock in g.hold_list:
        if (stock not in g.target_list) and (stock not in g.high_limit_list):
            position = context.portfolio.positions[stock]
            close_position(position)
    position_count = len(context.portfolio.positions)
    if len(g.target_list) > position_count:
        value = context.portfolio.cash / (len(g.target_list) - position_count)
        for stock in g.target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == len(g.target_list):
                        break
```

技术说明：

  * **调仓机制** ：每周一对持仓进行检查和调整，确保持仓股票符合策略的筛选标准。

  * **风险控制** ：通过过滤涨停、跌停和停牌股票，降低持仓风险，并防止过度集中于单一标的。

4\. 日终持仓信息输出

```python
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
    for position in context.portfolio.positions.values():
        print('代码:{}'.format(position.security))
        print('成本价:{}'.format(format(position.avg_cost, '.2f')))
        print('现价:{}'.format(position.price))
        print('收益率:{}%'.format(format(100 * (position.price / position.avg_cost - 1), '.2f')))
        print('持仓(股):{}'.format(position.total_amount))
        print('市值:{}'.format(format(position.value, '.2f')))
        print('———————————————————————————————————')
```

技术说明：

  * **持仓信息输出** ：每日收盘后输出详细的持仓信息和成交记录，便于复盘和策略优化。

### 总结

**多因子量化选股策略** 通过综合考虑多个财务指标，结合严格的风险管理与动态调仓，旨在实现持续稳定的超额收益。该策略适合注重基本面分析和量化选股的投资者，通过定期筛选优质标的，动态调整持仓，以应对市场波动和变化。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
