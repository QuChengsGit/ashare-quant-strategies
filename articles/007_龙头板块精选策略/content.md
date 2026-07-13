# 7、龙头板块精选策略

# 1. 策略概述

该策略通过选取市场中的连板龙头股票，并利用聚宽因子进一步筛选，从而构建一个具有较高收益潜力的股票组合。策略结合了短期强势股和因子分析，旨在捕捉市场热点并获取超额收益。

# 2. 策略逻辑

  1. **选股** ：

     * 策略通过筛选连续涨停板的股票，确定市场中的龙头股。

     * 利用因子分析（如换手率）进一步筛选出最具潜力的龙头股。

     * 结合市场情绪与概念分析，最终形成一个多维度的优质股票池。

  2. **交易** ：

     * 每日监控股票池并分批买入符合条件的股票。

     * 对不再符合条件或达到持仓时间的股票进行卖出，以及时锁定收益或减少亏损。

  3. **风控措施** ：

     * 策略避免频繁交易，通过筛选停牌、新股、ST股等方式降低风险。

     * 在市场出现较大波动时，策略会根据市场情绪调整持仓。

# 3. 策略代码详细说明

## 3.1 初始化函数 (initialize)

```python
def initialize(context):
    # 使用真实价格交易
    set_option('use_real_price', True)
    # 防止未来数据
    set_option('avoid_future_data', True)
    # 设定日志级别，仅保留error级别以上的日志
    log.set_level('system', 'error')
    # 设置最大持仓数量
    g.ps = 10  # 同时持有的最高龙头股数量
    # 设定筛选因子
    g.jqfactor = 'VOL5'  # 5日平均换手率
    g.sort = True  # 按因子值从小到大排序
    # 每日调度任务
    run_daily(get_stock_list, '9:01')
    run_daily(buy, '09:30')
    run_daily(sell, '14:50')
    run_daily(print_position_info, '15:02')
```

**功能** ：初始化策略的基本设置，包括使用真实价格、设定最大持仓数量、筛选因子和调度任务。

## 3.2 选股模块 (get_stock_list)

```python
def get_stock_list(context):
    # 文本日期
    date = transform_date(context.previous_date, 'str')
    # 获取初始股票池
    initial_list = prepare_stock_list(date)
    # 获取涨停股票
    hl_list = get_hl_stock(initial_list, date)
    # 获取连板股票
    ccd = get_continue_count_df(hl_list, date, 20) if len(hl_list) != 0 else pd.DataFrame(index=[], data={'count':[], 'extreme_count':[]})
    # 筛选龙头股票
    M = ccd['count'].max() if len(ccd) != 0 else 0
    CCD = ccd[ccd['count'] == M] if M != 0 else pd.DataFrame(index=[], data={'count':[], 'extreme_count':[]})
    lt = list(CCD.index)
    # 因子筛选
    df = get_factor_filter_df(context, lt, g.jqfactor, g.sort)
    stock_list = list(df.index)
    # 根据持仓情况截取股票列表
    g.target_list = stock_list[:(g.ps - len(context.portfolio.positions))]
```

**功能** ：筛选出符合条件的龙头股票，并根据持仓情况调整最终的目标股票池。

## 3.3 交易模块 (buy, sell)

```python
def buy(context):
    current_data = get_current_data()
    value = context.portfolio.total_value / g.ps
    for s in g.target_list:
        if context.portfolio.available_cash / current_data[s].last_price > 100:
            if current_data[s].last_price == current_data[s].high_limit:
                order_value(s, value, LimitOrderStyle(current_data[s].day_open))
            else:
                order_value(s, value, MarketOrderStyle(current_data[s].day_open))
            print('买入' + s)
```

**功能** ：根据选股结果进行买入操作，开盘涨停则使用限价单排队，否则使用市价单即时买入。

```python
def sell(context):
    hold_list = list(context.portfolio.positions)
    current_data = get_current_data()
    for s in hold_list:
        if not current_data[s].last_price == current_data[s].high_limit:
            if context.portfolio.positions[s].closeable_amount != 0:
                start_date = transform_date(context.portfolio.positions[s].init_time, 'str')
                target_date = get_shifted_date(start_date, 2, 'T')
                current_date = transform_date(context.current_dt, 'str')
                cost = context.portfolio.positions[s].avg_cost
                price = context.portfolio.positions[s].price
                ret = 100 * (price / cost - 1)
                if current_date >= target_date or ret > 0:
                    if current_data[s].last_price > current_data[s].low_limit:
                        order_target_value(s, 0)
                        print('卖出' + s)
```

**功能** ：卖出不再符合条件的股票，包括持有时间超过两天或已经盈利的股票。

## 3.4 日期处理函数 (transform_date, get_shifted_date)

```python
def transform_date(date, date_type):
    if type(date) == str:
        dt_date = dt.datetime.strptime(date, '%Y-%m-%d')
    elif type(date) == dt.datetime:
        dt_date = date
    elif type(date) == dt.date:
        dt_date = dt.datetime(date.year, date.month, date.day)
    return {'str': dt_date.strftime('%Y-%m-%d'), 'dt': dt_date, 'd': dt_date.date()}[date_type]
def get_shifted_date(date, days, days_type='T'):
    d_date = transform_date(date, 'd')
    yesterday = d_date - dt.timedelta(days=1)
    if days_type == 'T':
        trade_days = [i.strftime('%Y-%m-%d') for i in list(get_all_trade_days())]
        last_trade_date = next(d for d in trade_days if d < str(yesterday))
        shifted_date = trade_days[trade_days.index(last_trade_date) + days]
    return shifted_date
```

**功能** ：提供日期格式转换与交易日计算的功能，用于交易逻辑中的时间判断。

## 3.5 过滤函数 (filter_new_stock, filter_st_stock, 等)

```python
def filter_new_stock(initial_list, date, days=50):
    d_date = transform_date(date, 'd')
    return [stock for stock in initial_list if d_date - get_security_info(stock).start_date > dt.timedelta(days=days)]
def filter_st_stock(initial_list, date):
    str_date = transform_date(date, 'str')
    if get_shifted_date(str_date, 0, 'N') != get_shifted_date(str_date, 0, 'T'):
        str_date = get_shifted_date(str_date, -1, 'T')
    df = get_extras('is_st', initial_list, start_date=str_date, end_date=str_date, df=True)
    return df[df['is_st'] == False].index.tolist()
```

**功能** ：过滤不符合条件的新股、ST股、停牌股等。

## 3.6 打印持仓信息 (print_position_info)

```python
def print_position_info(context):
    position_percent = 100 * context.portfolio.positions_value / context.portfolio.total_value
    record(仓位=round(position_percent, 2))
    for position in context.portfolio.positions.values():
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print(f'代码:{securities} 成本价:{format(cost, ".2f")} 现价:{price} 收益率:{format(ret, ".2f")}% 持仓(股):{amount} 市值:{format(value, ".2f")}')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
```

**功能** ：打印每日持仓信息和当日交易记录，方便跟踪和分析策略表现。

# 4. 策略总结

**“龙头板块精选策略”** 通过筛选市场中的龙头股并结合因子分析，旨在捕捉市场中最有潜力的股票。该策略既关注市场情绪的变化，又通过因子分析提升选股的精准度，是一种高效的短线交易策略，适合在市场热点轮动中获取超额收益的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
