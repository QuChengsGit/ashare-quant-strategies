# 72、动态回归加速选股策略

### 策略介绍

**动态回归加速选股策略** 是一种结合了多因子选股和动量反转策略的加速版选股方法。该策略通过对市场进行筛选，选择出符合特定财务和技术指标的股票。核心在于使用OLS回归模型评估股票的单边上涨趋势，并结合动量反转策略在市场中获得超额收益。策略每隔固定天数进行一次调仓操作，极大提升了策略的运行效率，同时动态调整持仓以应对市场变化。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 使用真实价格交易
    set_option('use_real_price', True)
    # 避免未来数据
    set_option("avoid_future_data", True)
    # 设置日志级别为error
    log.set_level('order', 'error')
    # 设置固定滑点
    set_slippage(FixedSlippage(0.002))
    # 设置交易费用
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 初始化全局变量
    g.counter = 0
    g.arg_rsquared_min = 0.8  # OLS的R方最小值，用于判断全天均匀上涨
    g.arg_close_rate = 0.052  # 收盘价涨幅下限
    g.arg_volume_days = 5  # 成交量回看天数
    g.arg_volume_multi = 2  # 成交量大于days均值的倍数
    g.arg_buy_max = 10  # 持仓股票的最大数目
    g.buy_min_ratio = 0.4  # 买入时要达到的比例
    g.arg_hold_max = 20  # 单只股票持仓时间上限
    g.hold_days = g.arg_hold_max - 1  # 初始化持仓日数记录
    g.stocks = []  # 股票池
    g.choice = 1000  # 初选股票数量
    g.etf = "518880.XSHG"  # 黄金ETF代码
    g.hold_list = []  # 当前持仓的全部股票
    g.yesterday_HL_list = []  # 记录持仓中昨日涨停的股票
    # 运行函数
    run_daily(before_market_open, time='before_open')
    run_daily(trade, time='14:55')
    run_daily(check_limit_up, time='14:00', reference_security='000852.XSHG')
```

技术说明：

  * **基准设定** ：沪深300指数被设定为基准。

  * **交易费用** ：设置较低的交易费用以模拟实际交易环境。

  * **滑点设置** ：设置固定滑点为0.002，以模拟交易中的实际市场冲击成本。

  * **调仓频率** ：通过控制持仓时间和计数器，实现每隔一段时间的调仓操作，以提高策略运行效率。

2\. 开盘前选股逻辑

```python
def before_market_open(context):
    yesterday = context.previous_date
    # 获取持仓股票列表和昨日涨停的股票列表
    g.hold_list = [s for s in context.portfolio.positions]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=yesterday, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.yesterday_HL_list = list(df.code)
    else:
        g.yesterday_HL_list = []
    # 获取股票池，按市值排序
    fundamentals_data = get_fundamentals(query(valuation.code, valuation.market_cap).order_by(valuation.market_cap.asc()).filter(valuation.market_cap < 160).limit(g.choice))
    stocks = list(fundamentals_data['code'])
    # 各种过滤条件
    current_data = get_current_data()
    stocks = [s for s in stocks if not current_data[s].paused
              and not current_data[s].is_st
              and 'N' not in current_data[s].name
              and '退' not in current_data[s].name
              and current_data[s].low_limit < current_data[s].day_open < current_data[s].high_limit
              and s[0] != '4' and s[0] != '8' and s[:2] != '68'
              and s not in g.hold_list]
    # 过滤上市时间小于250天的股票
    g.stocks = [stock for stock in stocks if yesterday - get_security_info(stock).start_date > datetime.timedelta(days=250)]
    log.info('股票数量{}'.format(len(g.stocks)))
```

技术说明：

  * **股票筛选** ：首先根据市值对股票进行排序，并进行多重过滤，包括过滤掉ST股票、次新股、涨跌停股票等，最终筛选出合适的股票池。

  * **涨停股票处理** ：记录昨日涨停的股票，以便在后续交易决策中进行处理。

3\. 选股与交易逻辑

```python
def get_stocks(context):
    current_data = get_current_data()
    stock_chosen = []
    stock_chosen_mom = []
    for stock in g.stocks:
        history_data = attribute_history(stock, unit='1d', count=g.arg_volume_days, fields=['open', 'close', 'volume'])
        history_volume = np.mean(history_data['volume'])
        if np.isnan(history_volume):
            continue
        df_stock_data = get_price(stock, start_date=context.current_dt.replace(hour=9, minute=30, second=0),
                                  end_date=context.current_dt, frequency='1m', fields=['open', 'close', 'high', 'volume'])
        if df_stock_data['volume'].sum() < g.arg_volume_multi * history_volume:
            continue
        if (current_data[stock].last_price - current_data[stock].day_open) / current_data[stock].day_open < g.arg_close_rate:
            continue
        if current_data[stock].high_limit <= df_stock_data['high'].iloc[-1]:
            continue
        Y = df_stock_data['close'].values
        X = sm.add_constant(np.arange(Y.shape[0]))
        ols_result = sm.OLS(Y, X).fit()
        flag_keep_up = (ols_result.rsquared > g.arg_rsquared_min) & (ols_result.params[1] > 0)
        if not flag_keep_up:
            continue
        stock_chosen.append(stock)
        stock_chosen_mom.append((history_data['close'].iloc[-1] - history_data['open'].iloc[-1]) / history_data['open'].iloc[-1])
    stocks = [stock_chosen[i] for i in np.argsort(stock_chosen_mom)[:g.arg_buy_max]]
    log.info(f"可选 {stocks}")
    return stocks
def trade(context):
    g.hold_days += 1
    if g.hold_days < g.arg_hold_max:
        return
    stocks = get_stocks(context)
    for stock in context.portfolio.positions.keys():
        if stock == g.etf:
            continue
        order_target_value(stock, 0)
    count_min = int(g.buy_min_ratio * g.arg_buy_max)
    if len(stocks) < count_min:
        if g.etf:
            order_value(g.etf, context.portfolio.available_cash)
        return
    val = context.portfolio.total_value / (g.arg_buy_max - len(context.portfolio.positions))
    for stock in stocks:
        if len(context.portfolio.positions) >= g.arg_buy_max:
            break
        if g.etf and context.portfolio.available_cash < val and g.etf in context.portfolio.positions:
            order_value(g.etf, -val)
        order_value(stock, val)
    if len(context.portfolio.positions) > 0:
        g.hold_days = 0
    if g.etf:
        order_value(g.etf, context.portfolio.available_cash)
```

技术说明：

  * **动量反转策略** ：根据动量反转的原理，选择动量最小的股票进行买入操作。

  * **交易执行** ：先卖出当前不符合条件的股票，再根据选股结果买入新股。同时通过黄金ETF的配置，管理闲置资金。

4\. 涨停股票处理

```python
def check_limit_up(context):
    now_time = context.current_dt
    for stock in g.yesterday_HL_list:
        current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
        if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
            log.info("[%s]涨停打开，卖出" % (stock))
            order_value(stock, 0)
        else:
            log.info("[%s]
涨停，继续持有" % (stock))
    if g.etf:
        order_value(g.etf, context.portfolio.available_cash)
```

技术说明：

  * **涨停股票的提前处理** ：对于昨日涨停的股票，如果在次日未能继续涨停，则会提前卖出以规避风险；否则则继续持有。

### 总结

**动态回归加速选股策略** 通过合理的因子筛选、动态调整和动量反转策略的结合，实现了股票池的高效选择与持仓管理。策略有效利用OLS回归模型筛选单边上涨的股票，并通过定期调仓和黄金ETF的资金管理，确保组合在不同市场环境中的稳定表现。这一策略特别适合于寻求在复杂市场环境中获取稳健收益的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
