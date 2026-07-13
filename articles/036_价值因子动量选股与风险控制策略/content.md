# 36、价值因子动量选股与风险控制策略

# 1. 策略概述

该策略结合了股息率、PEG、低价股等多因子筛选方法，并通过动态调仓和风险控制机制来优化投资组合。每月初根据因子模型选取价值股，同时对市场情绪较为敏感的股票进行过滤。策略在每月初调仓，并在尾盘根据实时数据进行风险控制，确保组合的稳健性和收益的稳定性。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (initialize)

此模块初始化策略参数、设置交易基准、配置滑点和交易成本，并调度策略的运行时间。

```python
def initialize(context):
    log.set_level('order', 'error')  # 设定日志输出等级
    set_option('use_real_price', True)  # 设定使用真实价格
    set_option('avoid_future_data', True)  # 防止未来函数
    set_benchmark('000905.XSHG')  # 设置基准为中证500
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    # 初始化全局变量
    g.no_trading_today_signal = False  # 是否为资金再平衡日
    g.stock_num = 5  # 持仓股票数量
    g.choice = []  # 选股池
    g.just_sold = []  # 本月已卖出的股票
    # 调度交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00')
    run_monthly(my_Trader, 1, time='9:30', force=True)
    run_monthly(go_Trader, 1, time='14:55', force=True)
    run_daily(close_account, '14:30')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
```

## 2.2 策略执行模块 (my_Trader)

此模块根据股息率、PEG等因子筛选股票，并将最终筛选的结果保存到全局变量中，供后续买入操作使用。

```python
def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)  # 过滤科创板和北交所股票
    stocks = get_dividend_ratio_filter_list(context, stocks, False, 0, 0.25)  # 筛选股息率前25%的股票
    stocks = get_peg(context, stocks)  # 进一步根据PEG筛选
    choice = filter_st_stock(stocks)  # 过滤ST股票
    choice = filter_paused_stock(choice)  # 过滤停牌股票
    choice = filter_limitup_stock(context, choice)  # 过滤涨停股票
    choice = filter_limitdown_stock(context, choice)  # 过滤跌停股票
    choice = filter_highprice_stock(context, choice)  # 过滤高价股（股价高于10元）
    g.choice = choice[:g.stock_num]  # 保存最终选股结果
```

## 2.3 执行交易模块 (go_Trader)

此模块在每月初执行调仓操作，卖出不在选股池中的股票，并买入新的股票。

```python
def go_Trader(context):
    if not g.no_trading_today_signal:
        g.just_sold = []  # 每月清空已卖出的股票列表
        cdata = get_current_data()
        choice = g.choice
        # 卖出不在选股池中的股票
        for s in context.portfolio.positions:
            if s not in choice:
                log.info('Sell', s, cdata[s].name)
                order_target(s, 0)
        # 买入新的股票
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count:
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in choice:
                if s not in context.portfolio.positions:
                    log.info('buy', s, cdata[s].name)
                    order = order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break
```

## 2.4 资金再平衡模块 (close_account)

该模块在特定日期内将持仓清零，以便进行资金再平衡。

```python
def close_account(context):
    if g.no_trading_today_signal:
        position_count = context.portfolio.positions
        if len(position_count) != 0:
            for stock in position_count:
                position = context.portfolio.positions[stock]
                close_position(position)
                log.info("卖出[%s]" % (stock))
```

## 2.5 过滤与因子筛选模块

这些模块用于对股票池进行各种过滤操作，并根据股息率和PEG因子筛选股票。

```python
# 获取PEG因子并筛选股票
def get_peg(context, stocks):
    q = query(valuation.code,
              valuation.pe_ratio / indicator.inc_net_profit_year_on_year,  # PEG因子
              indicator.roe / valuation.pb_ratio,  # PB-ROE因子
              indicator.roe,
              valuation.pb_ratio).filter(
                  valuation.pe_ratio / indicator.inc_net_profit_year_on_year < 0,
                  valuation.pb_ratio < 3,
                  valuation.code.in_(stocks))
    df_fundamentals = get_fundamentals(q, date=None)
    stocks = list(df_fundamentals.code)
    df = get_fundamentals(query(valuation.code).filter(valuation.code.in_(stocks)).order_by(valuation.market_cap.asc()))
    return list(df.code)
# 获取股息率并筛选股票
def get_dividend_ratio_filter_list(context, stock_list, sort, p1, p2):
    time1 = context.previous_date
    time0 = time1 - datetime.timedelta(days=365)
    interval = 1000
    list_len = len(stock_list)
    q = query(finance.STK_XR_XD.code,
              finance.STK_XR_XD.a_registration_date,
              finance.STK_XR_XD.bonus_amount_rmb).filter(
                  finance.STK_XR_XD.a_registration_date >= time0,
                  finance.STK_XR_XD.a_registration_date <= time1,
                  finance.STK_XR_XD.code.in_(stock_list[:min(list_len, interval)]))
    df = finance.run_query(q)
    if list_len > interval:
        df_num = list_len // interval
        for i in range(df_num):
            q = query(finance.STK_XR_XD.code,
                      finance.STK_XR_XD.a_registration_date,
                      finance.STK_XR_XD.bonus_amount_rmb).filter(
                          finance.STK_XR_XD.a_registration_date >= time0,
                          finance.STK_XR_XD.a_registration_date <= time1,
                          finance.STK_XR_XD.code.in_(stock_list[interval * (i + 1):min(list_len, interval * (i + 2))]))
            temp_df = finance.run_query(q)
            df = df.append(temp_df)
    dividend = df.fillna(0).set_index('code').groupby('code').sum()
    temp_list = list(dividend.index)
    q = query(valuation.code, valuation.market_cap).filter(valuation.code.in_(temp_list))
    cap = get_fundamentals(q, date=time1).set_index('code')
    DR = pd.concat([dividend, cap], axis=1, sort=False)
    DR['dividend_ratio'] = (DR['bonus_amount_rmb'] / 10000) / DR['market_cap']
    DR = DR.sort_values(by=['dividend_ratio'], ascending=sort)
    return list(DR.index)[int(p1 * len(DR)):int(p2 * len(DR))]
```

## 2.6 风险控制模块 (check_limit_up)

该模块在尾盘前对持仓股票进行检查，如果涨停打开则卖出。

```python
def check_limit_up(context):
    if not g.no_trading_today_signal:
        position_count = len(context.portfolio.positions)
        if g.stock_num > position_count and position_count != 0:
            my_Trader(context)  # 重新计算股票池
            cdata = get_current_data()
            psize = context.portfolio.available_cash / (g.stock_num - position_count)
            for s in g.choice:
                if s not in context.portfolio.positions and s not in g.just_sold:
                    order = order_value(s, psize)
                    if len(context.portfolio.positions) == g.stock_num:
                        break
        # 获取昨日涨停的股票列表
        current_data = get_current_data()
        if g.high_limit_list:
            for stock in g.high_limit_list:
                if current_data[stock].last_price < current_data[stock].high_limit:
                    order_target(stock, 0)
                    g.just_sold.append(stock)
```

## 2.7 辅助模块

这些模块包括买入、卖出、平仓等常用操作的封装。

```python
def open_position(security, value):
    order = order_target_value(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    security = position.security
    order = order_target_value(security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
def order_target_value_(security, value):
    if value == 0:
        log.debug("Selling out %s" % (security))
    else:
        log.debug("Order %s to value %f" % (security, value))
    return order_target_value(security, value)
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if stock[0] != '4' and stock[0] != '8' and stock[:2] != '68']
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < current_data[stock].high_limit * 0.97]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] > current_data[stock].low_limit * 1.04]
def filter_highprice_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < 10]
```

# 3. 策略优化建议

  1. **优化调仓频率** ：考虑在每月初调仓的基础上，增加在月中和月底的风险检查，以避免突发的市场风险。

  2. **引入止损机制** ：对于已经出现较大回撤的股票，可以考虑加入止损机制，避免更大损失。

  3. **增加因子多样性** ：在现有因子筛选的基础上，增加更多的技术指标和市场情绪因子，以提高策略的适应性和抗风险能力。

通过这些模块的优化和组合，该策略在保证收益的同时，尽量降低了市场波动带来的风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
