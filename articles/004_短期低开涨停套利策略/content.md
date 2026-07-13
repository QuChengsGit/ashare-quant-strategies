# 4、短期低开涨停套利策略

# 1. 策略概述

该策略主要针对A股市场的短期低开涨停股票，基于市场情绪和技术分析，捕捉市场中的短期套利机会。通过筛选前一交易日涨停但未持续连板的股票，结合当日低开信号，进行短线买入，日内通过止盈或止损卖出，力求在较短时间内获取收益。

**短期低开涨停套利策略完整代码下载方式请见文末** 。

# 2. 策略逻辑

  1. **选股逻辑** ：

     * 筛选出前一交易日涨停但未持续连板的股票。

     * 从中选择相对位置较低且当日低开的股票。

     * 满足条件的股票进行均仓买入。

  2. **卖出逻辑** ：

     * 日内分两次执行卖出操作：

       1. 上午通过价格突破高点或止盈卖出。

       2. 下午临近收盘通过价格未达高点的止损卖出。

  3. **风控措施** ：

     * 使用严格的止盈和止损机制，确保风险可控。

     * 过滤ST、次新股、科创板等高风险股票。

# 3. 策略代码详细说明

## 3.1 初始化函数 (initialize)

```python
def initialize(context):
    # 系统设置
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option('avoid_future_data', True)  # 防止未来数据干扰
    log.set_level('system', 'error')  # 过滤系统日志，避免过多冗余信息
    # 每日调度任务
    run_daily(buy, '09:30')  # 开盘后进行选股和买入操作
    run_daily(sell, '11:28')  # 上午卖出操作
    run_daily(sell, '14:50')  # 下午卖出操作
```

**功能** ：初始化策略的基本配置，设定日志级别和每日的交易任务。策略在每日开盘后、上午收盘前和下午收盘前执行相应的买卖操作。

## 3.2 选股逻辑与买入 (buy)

```python
def buy(context):
    # 基础信息
    date = transform_date(context.previous_date, 'str')
    current_data = get_current_data()
    # 获取昨日涨停的股票
    initial_list = prepare_stock_list(date)
    hl_list = get_hl_stock(initial_list, date)
    if hl_list:
        # 获取非连板涨停的股票
        ccd = get_continue_count_df(hl_list, date, 10)
        lb_list = list(ccd.index)
        stock_list = [s for s in hl_list if s not in lb_list]
        # 计算相对位置，选择位置较低的股票
        rpd = get_relative_position_df(stock_list, date, 60)
        rpd = rpd[rpd['rp'] <= 0.5]
        stock_list = list(rpd.index)
        # 筛选出低开的股票
        if stock_list:
            df = get_price(stock_list, end_date=date, frequency='daily', fields=['close'], count=1, panel=False, fill_paused=False, skip_paused=True).set_index('code')
            df['open_pct'] = [current_data[s].day_open / df.loc[s, 'close'] for s in stock_list]
            df = df[(0.96 <= df['open_pct']) & (df['open_pct'] <= 0.97)]  # 仅选择低开3%左右的股票
            stock_list = list(df.index)
        # 买入操作
        if not context.portfolio.positions and stock_list:
            for s in stock_list:
                order_target_value(s, context.portfolio.total_value / len(stock_list))
                log.info(f"买入: {get_security_info(s, date).display_name} ({s})")
```

**功能** ：筛选出符合条件的股票并进行买入。股票需满足以下条件：前一日涨停、未连板、相对位置较低且当日低开。

## 3.3 卖出逻辑 (sell)

```python
def sell(context):
    # 基础信息
    date = transform_date(context.previous_date, 'str')
    current_data = get_current_data()
    # 上午止盈卖出
    if str(context.current_dt)[-8:] == '11:28:00':
        for s in list(context.portfolio.positions):
            if (context.portfolio.positions[s].closeable_amount != 0 and
                current_data[s].last_price < current_data[s].high_limit and
                current_data[s].last_price > context.portfolio.positions[s].avg_cost):
                order_target_value(s, 0)
                log.info(f"止盈卖出: {get_security_info(s, date).display_name} ({s})")
    # 下午止损卖出
    if str(context.current_dt)[-8:] == '14:50:00':
        for s in list(context.portfolio.positions):
            if (context.portfolio.positions[s].closeable_amount != 0 and
                current_data[s].last_price < current_data[s].high_limit):
                order_target_value(s, 0)
                log.info(f"止损卖出: {get_security_info(s, date).display_name} ({s})")
```

**功能** ：根据不同的市场情况在上午和下午分别执行止盈和止损操作。确保在当天结束前清仓，避免隔夜风险。

## 3.4 辅助函数与工具

日期处理函数

```python
def transform_date(date, date_type):
    if isinstance(date, str):
        dt_date = dt.datetime.strptime(date, '%Y-%m-%d')
    elif isinstance(date, dt.datetime):
        dt_date = date
    elif isinstance(date, dt.date):
        dt_date = dt.datetime.combine(date, dt.datetime.min.time())
    else:
        raise ValueError("Invalid date format")
    date_mapping = {
        'str': dt_date.strftime('%Y-%m-%d'),
        'dt': dt_date,
        'd': dt_date.date()
    }
    return date_mapping[date_type]
def get_shifted_date(date, days, days_type='T'):
    d_date = transform_date(date, 'd')
    yesterday = d_date + dt.timedelta(-1)
    if days_type == 'N':
        shifted_date = yesterday + dt.timedelta(days + 1)
    elif days_type == 'T':
        all_trade_days = [i.strftime('%Y-%m-%d') for i in list(get_all_trade_days())]
        if str(yesterday) in all_trade_days:
            shifted_date = all_trade_days[all_trade_days.index(str(yesterday)) + days + 1]
        else:
            for i in range(100):
                last_trade_date = yesterday - dt.timedelta(i)
                if str(last_trade_date) in all_trade_days:
                    shifted_date = all_trade_days[all_trade_days.index(str(last_trade_date)) + days + 1]
                    break
    return str(shifted_date)
```

**功能** ：处理日期转换与日期偏移操作，确保获取准确的交易日信息。

股票筛选与过滤

```python
def filter_new_stock(initial_list, date, days=250):
    d_date = transform_date(date, 'd')
    return [stock for stock in initial_list if d_date - get_security_info(stock).start_date > dt.timedelta(days=days)]
def filter_st_stock(initial_list, date):
    str_date = transform_date(date, 'str')
    if get_shifted_date(str_date, 0, 'N') != get_shifted_date(str_date, 0, 'T'):
        str_date = get_shifted_date(str_date, -1, 'T')
    df = get_extras('is_st', initial_list, start_date=str_date, end_date=str_date, df=True).T
    return list(df[df['is_st'] == False].index)
def filter_kcbj_stock(initial_list):
    return [stock for stock in initial_list if not stock.startswith(('4', '8', '68'))]
def filter_paused_stock(initial_list, date):
    df = get_price(initial_list, end_date=date, frequency='daily', fields=['paused'], count=1, panel=False, fill_paused=True)
    return list(df[df['paused'] == 0].code)
```

**功能** ：过滤高风险股票，包括次新股、ST股、科创板股票和停牌股票，确保筛选出的股票更稳定可靠。

获取每日初始股票池与涨停股票

```python
def prepare_stock_list(date):
    initial_list = get_all_securities('stock', date).index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_new_stock(initial_list, date)
    initial_list = filter_st_stock(initial_list, date)
    initial_list = filter_paused_stock(initial_list, date)
    return initial_list
def get_hl_stock(initial_list, date):
    df = get_price(initial_list, end_date=date, frequency='daily', fields=['close','high','high_limit'], count=1, panel=False, fill_paused=False, skip_paused=False)
    df =
 df.dropna()  # 去除停牌股票
    return list(df[df['close'] == df['high_limit']].code)
```

**功能** ：获取当日符合条件的初始股票池，并筛选出当日涨停股票。

涨停次数与连板检测

```python
def get_hl_count_df(hl_list, date, watch_days):
    df = get_price(hl_list, end_date=date, frequency='daily', fields=['low','close','high_limit'], count=watch_days, panel=False, fill_paused=False, skip_paused=False)
    df.index = df.code
    hl_count_list = []
    extreme_hl_count_list = []
    for stock in hl_list:
        df_sub = df.loc[stock]
        hl_days = df_sub[df_sub.close == df_sub.high_limit].high_limit.count()
        extreme_hl_days = df_sub[df_sub.low == df_sub.high_limit].high_limit.count()
        hl_count_list.append(hl_days)
        extreme_hl_count_list.append(extreme_hl_days)
    return pd.DataFrame(index=hl_list, data={'count': hl_count_list, 'extreme_count': extreme_hl_count_list})
def get_continue_count_df(hl_list, date, watch_days):
    df = pd.DataFrame()
    for d in range(2, watch_days + 1):
        HLC = get_hl_count_df(hl_list, date, d)
        CHLC = HLC[HLC['count'] == d]
        df = df.append(CHLC)
    stock_list = list(set(df.index))
    ccd = pd.DataFrame()
    for s in stock_list:
        tmp = df.loc[[s]]
        if len(tmp) > 1:
            M = tmp['count'].max()
            tmp = tmp[tmp['count'] == M]
        ccd = ccd.append(tmp)
    return ccd.sort_values(by='count', ascending=False) if not ccd.empty else ccd
```

**功能** ：计算股票的涨停次数和连板情况，避免选择连续涨停的高风险股票。

计算相对位置

```python
def get_relative_position_df(stock_list, date, watch_days):
    if stock_list:
        df = get_price(stock_list, end_date=date, fields=['high', 'low', 'close'], count=watch_days, fill_paused=False, skip_paused=False, panel=False).dropna()
        close = df.groupby('code').apply(lambda df: df.iloc[-1, -1])
        high = df.groupby('code').apply(lambda df: df['high'].max())
        low = df.groupby('code').apply(lambda df: df['low'].min())
        result = pd.DataFrame()
        result['rp'] = (close - low) / (high - low)
        return result
    else:
        return pd.DataFrame(columns=['rp'])
```

**功能** ：计算股票在一定时间内的相对位置，帮助识别价格较低的潜在买入机会。

# 4. 策略总结

**"短期低开涨停套利策略"** 是一个基于市场情绪的短线交易策略，适合追求快速收益的投资者。策略通过精确筛选涨停但非连板且低开的股票进行短线操作，严格的止盈止损机制确保了风险的可控性，日内交易的特点减少了隔夜风险。这种高频次、低持仓时间的策略能够有效捕捉市场中的短期波动机会。

## 短期低开涨停套利策略完整代码

下载链接: <https://pan.baidu.com/s/1Qk4Xjxir-Wn4QNjmBcKNkQ>

提取码: ydda

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
