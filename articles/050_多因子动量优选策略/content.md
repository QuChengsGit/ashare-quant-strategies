# 50、多因子动量优选策略

# 1. 策略概述

**多因子动量优选策略** 是一种基于多因子选股和动量策略相结合的投资策略。该策略通过多因子模型筛选优质股票，并结合动量指标确定最终的投资标的。此策略在考虑盈利质量和成长性的同时，通过动量因子判断股票的市场表现趋势，并在回测中规避了ST股、次新股及涨停股的风险。

# 2. 策略各部分功能代码详细技术文档说明

## 2.1 策略初始化 (initialize)

初始化策略的基本设置，包括基准指数、交易滑点、交易成本等参数，并定义全局变量。此策略每月进行一次调仓，同时设定了日常的股票筛选和涨停股检测。

```python
def initialize(context):
    # 设定中证500作为基准
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 避免使用未来数据
    set_option("avoid_future_data", True)
    # 过滤掉低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 8  # 持股数量
    g.limit_days = 20  # 检查最近20天内涨停的股票
    g.hold_list = []  # 当前持仓股票列表
    g.history_hold_list = []  # 历史持仓股票列表
    g.not_buy_again_list = []  # 不再买入的股票列表
    # 设置交易时间，每天和每月运行
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(monthly_adjustment, monthday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
```

## 2.2 单因子选股函数 (get_single_factor_list)

该函数根据指定的因子对股票进行排序，筛选出前一定比例的股票。

```python
def get_single_factor_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    s_score = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1
                                )[jqfactor].iloc[0].dropna().sort_values(ascending=sort)
    return s_score.index[int(p1 * len(stock_list)):int(p2 * len(stock_list))].tolist()
```

## 2.3 选股模块 (get_stock_list)

通过多因子筛选和组合，选出潜在的投资标的。因子包括扣非利润比、长期盈利增长率、PEG等。

```python
def get_stock_list(context):
    # 去掉次新股
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 过滤科创板和ST股
    initial_list = filter_kcb_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 1. 扣非利润比前30%
    sg_list = get_single_factor_list(context, initial_list, 'adjusted_profit_to_total_profit', False, 0, 0.3)
    # 2. 综合成长因子
    factor_list = [
        'short_term_predicted_earnings_growth',
        'long_term_predicted_earnings_growth',
        'net_profit_growth_rate',
        'earnings_growth'
    ]
    factor_values = get_factor_values(sg_list, factor_list, end_date=context.previous_date, count=1)
    df = pd.DataFrame(index=sg_list)
    for factor in factor_list:
        df[factor] = factor_values[factor].iloc[0]
    df['total_score'] = 0.2 * df['short_term_predicted_earnings_growth'] + 0.4 * df['long_term_predicted_earnings_growth'] + 0.2 * df['net_profit_growth_rate'] + 0.2 * df['earnings_growth']
    ms_list = df.sort_values(by=['total_score'], ascending=False).index[:int(0.08 * len(df))].tolist()
    # 3. 综合PEG和市值筛选
    peg_list = get_single_factor_list(context, ms_list, 'PEG', True, 0, 0.2)
    peg_list = get_single_factor_list(context, ms_list, 'turnover_volatility', True, 0, 0.8)
    peg_list = sorted_by_circulating_market_cap(peg_list)
    return peg_list
```

## 2.4 准备股票池 (prepare_stock_list)

在每天交易前准备股票池，并更新持仓记录，避免重复买入最近交易过的股票。

```python
def prepare_stock_list(context):
    g.hold_list = list(context.portfolio.positions)
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        temp_set = temp_set.union(set(hold_list))
    g.not_buy_again_list = list(temp_set)
    # 获取昨日涨停的持仓股
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'],
                       count=1, panel=False)
        g.high_limit_list = df.query('close==high_limit and paused==0')['code'].tolist()
```

## 2.5 调整持仓 (monthly_adjustment)

每月初根据选股结果调整持仓，剔除不符合条件的股票，并新买入优质股票。

```python
def monthly_adjustment(context):
    # 获取应买入列表
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limit_stock(context, target_list)
    # 去除最近涨停过和最近买过的股票
    recent_limit_up_list = get_recent_limit_up_stock(context, target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in target_list if stock not in black_list]
    # 排除下降趋势明显的股票
    h_ma = history(20 + 20, '1d', 'close', target_list).rolling(window=20).mean().iloc[20:]
    X = np.arange(len(h_ma))
    tmp_target_list = []
    for stock in target_list:
        MA_N_Arr = h_ma[stock].values
        MA_N_Arr = MA_N_Arr - MA_N_Arr[0]
        slope = round(sm.OLS(MA_N_Arr, X).fit().params[0] * 100, 1)
        if slope >= -2 or stock in g.hold_list:
            tmp_target_list.append(stock)
    target_list = tmp_target_list
    # 调仓
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % stock)
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持有[%s]" % stock)
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

## 2.6 调整昨日涨停股票 (check_limit_up)

每日检查昨日涨停股票，若今日涨停打开，则卖出该股票。

```python
def check_limit_up(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info("[%s]涨停打开，卖出" % stock)
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % stock)
```

## 2.7 辅助过滤函数

多个过滤函数用于筛选符合条件的股票，如过滤ST股、次新股、停牌股和涨停股。

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
            current_data[stock].is_st or
            'ST' in current_data[stock].name or
            '*' in current_data[stock].name or
 '退' in current_data[stock].name)]
def filter_limit_stock(context, stock_list):
    current_data = get_current_data()
    holdings = list(context.portfolio.positions)
    return [stock for stock in stock_list if (stock in holdings) or
            current_data[stock].low_limit < current_data[stock].last_price < current_data[stock].high_limit]
def filter_kcb_stock(stock_list):
    return [stock for stock in stock_list if not stock.startswith('68')]
```

# 3. 优化建议

  1. **动态调整权重** ：可以通过引入市场情绪指标或者宏观经济因子，动态调整因子的权重以应对不同市场环境。

  2. **止盈止损机制** ：为减少回撤，建议引入止盈止损机制，及时锁定利润或控制亏损。

  3. **多时间周期分析** ：结合不同时间周期的动量指标，例如增加短期和中期动量的权重，进一步优化策略的稳定性。

4\. 总结

**多因子动量优选策略** 通过对多因子进行综合评分和动量分析，精选出具备成长性和市场表现良好的股票进行投资。策略严格规避了高风险股票，并结合了趋势分析，力求在风险控制的前提下获取稳健的收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
