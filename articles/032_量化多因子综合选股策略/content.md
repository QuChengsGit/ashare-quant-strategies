# 32、量化多因子综合选股策略

# 1. 策略概述

本策略基于多因子模型，综合考虑股票的财务指标、估值和市场表现，筛选出具有较高投资价值的股票。策略通过定期筛选股票池，使用评分机制对股票进行排序，并结合市值、成交量和涨幅等多个维度进行选股和调仓。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (initialize)

该模块用于设置策略的基础配置，包括初始化系统参数和全局变量、设定定时任务等。

```python
def initialize(context):
    # 设置系统参数
    set_option('use_real_price', True)
    set_slippage(PriceRelatedSlippage(0.00))
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 初始化全局变量
    g.chosen_stock_list = []  # 选出的股票列表
    g.sold_stock = {}         # 已卖出股票列表
    g.buy_stock_count = 4      # 购买股票数量
    g.score = 7               # 股票评分阈值
    g.buyrank = g.buy_stock_count * 2  # 输出可买入列表的个数
    g.sellrank = g.buy_stock_count * 2 # 筛选时保留的股票个数
    g.stock_selection_percent = 0.7  # 设置选取市值最大股票的百分比
    g.volume_days = 5         # 成交量计算天数
    g.increase_days = 60      # 涨幅计算天数
    g.score_weights = [2, 1, 1, 4, 4]  # 股票评分权重
    # 设置定时任务
    run_monthly(before_trading, 1, '09:29')
    run_daily(mysell, '09:30')
    run_daily(mybuy, '09:31')
    # 设置日志级别
    log.set_level('order', 'error')
    log.set_level('system', 'error')
    log.set_level('history', 'error')
```

### 2.2 选股模块 (get_stock_list)

该模块从基本面和市场数据出发，筛选出符合条件的股票池，并进行进一步的过滤和评分。

```python
def get_stock_list(context):
    # 获取股票的基本面数据
    q = query(
        valuation.code,
        valuation.pe_ratio,
        valuation.pb_ratio,
        indicator.inc_return,
        indicator.inc_total_revenue_year_on_year,
        indicator.inc_net_profit_year_on_year,
        valuation.market_cap
    ).filter(
        valuation.pe_ratio > 0,
        valuation.pb_ratio > 0,
        indicator.inc_return > 0,
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0
    )
    df = get_fundamentals(q)
    df = pd.DataFrame(df).dropna().sort_values(by='market_cap', ascending=False)
    print('本月股票总数: %s' % len(df))
    # 选取前N%的股票
    df = select_top_percent_stocks(df, g.stock_selection_percent)
    print('本月选中股票总数: {}% ({})'.format(g.stock_selection_percent * 100, len(df)))
    stock_list = list(df['code'])
    # 对股票列表进行多维度过滤
    stock_list = filter_st_stock(stock_list)
    stock_list = filter_paused_stock(stock_list)
    stock_list = filter_limitup_stock(context, stock_list)
    stock_list = filter_limitdown_stock(context, stock_list)
    stock_list = filter_kcbj_stock(stock_list)
    stock_list = ffscore_stock(context, g.score, stock_list, context.current_dt.date())
    print('本月股票池 %s 个' % len(stock_list))
    return stock_list
```

### 2.3 调仓模块 (my_adjust_position)

该模块根据当前持仓情况和选股结果，进行仓位调整，确保投资组合的持仓比例在合理范围内。

```python
def my_adjust_position(context, hold_stocks):
    free_value = context.portfolio.total_value
    maxpercent = 1.3 / g.buy_stock_count
    buycash = free_value / g.buy_stock_count
    for stock in context.portfolio.positions.keys():
        current_data = get_current_data()
        price1d = get_close_price(stock, 1)
        nosell_1 = context.portfolio.positions[stock].price >= current_data[stock].high_limit
        sell_2 = stock not in hold_stocks
        if sell_2 and not nosell_1:
            close_position(stock)
        else:
            current_percent = context.portfolio.positions[stock].value / context.portfolio.total_value
            if current_percent > maxpercent:
                order_target_value(stock, buycash)
```

### 2.4 卖出模块 (mysell)

根据筛选后的股票池，检查当前持仓并决定是否卖出不符合条件的股票。

```python
def mysell(context):
    g.chosen_stock_list = get_stock_rank_m_m(g.chosen_stock_list)
    my_adjust_position(context, g.chosen_stock_list)
```

### 2.5 买入模块 (mybuy)

在卖出股票后，根据资金状况和目标持仓数量，买入符合条件的股票。

```python
def mybuy(context):
    hold_stocks = g.chosen_stock_list
    if len(hold_stocks) < g.buy_stock_count:
        g.buy_stock_count = len(hold_stocks)
        log.info("Adjusted buy_stock_count to {} as there are fewer stocks in hold_stocks.".format(g.buy_stock_count))
    free_value = context.portfolio.total_value
    minpercent = 0.7 / g.buy_stock_count
    buycash = free_value / g.buy_stock_count
    free_cash = free_value - context.portfolio.positions_value
    min_buy = context.portfolio.total_value / (g.buy_stock_count * 10)
    for i in range(g.buy_stock_count):
        if len(context.portfolio.positions) >= g.buy_stock_count:
            break
        stock = hold_stocks[i]
        if free_cash <= min_buy:
            break
        position = context.portfolio.positions.get(stock)
        current_percent = position.value / context.portfolio.total_value if position else 0
        if current_percent >= minpercent:
            continue
        tobuy = min(free_cash, buycash - position.value) if position else min(buycash, free_cash)
        order_value(stock, tobuy)
        free_cash -= tobuy
```

### 2.6 评分筛选模块 (get_stock_rank_m_m)

该模块根据自定义的多因子评分对股票进行打分和排序，选出最优的股票进行投资。

```python
def get_stock_rank_m_m(stock_list):
    rank_stock_list = DataFrame(stock_list)
    rank_stock_list.rename(columns={0: 'code'}, inplace=True)
    rank_stock_list['circulating_market_cap'] = [get_fundamentals(query(valuation).filter(valuation.code == stock)).iloc[0]['circulating_market_cap'] for stock in rank_stock_list['code']]
    rank_stock_list['market_cap'] = [get_fundamentals(query(valuation).filter(valuation.code == stock)).iloc[0]['market_cap'] for stock in rank_stock_list['code']]
    volume_days_sum = [attribute_history(stock, g.volume_days, '1d', 'volume', df=False)['volume'].sum() for stock in rank_stock_list['code']]
    increase_period = [get_growth_rate(g.increase_days, stock) for stock in rank_stock_list['code']]
    current_price = [get_close_price(stock, 1, '1m') for stock in rank_stock_list['code']]
    min_price = min(current_price)
    min_increase_period = min(increase_period)
    min_volume = min(volume_days_sum)
    min_circulating_market_cap = min(rank_stock_list['circulating_market_cap'])
    min_market_cap = min(rank_stock_list['market_cap'])
    totalcount = [[i,
                   math.log(min_price / current_price[i]) * g.score_weights[0] +
                   math.log(min_volume / volume_days_sum[i]) * g.score_weights[1] +
                   math.log(min_increase_period / increase_period[i]) * g.score_weights[2] +
                   math.log(min_circulating_market_cap / rank_stock_list['circulating_market_cap'][i]) * g.score_weights[3] +
                   math.log(min_market_cap / rank_stock_list['market_cap'][i]) * g.score_weights[4]
                   ] for i in rank_stock_list.index]
    totalcount.sort(key=lambda x: x[1])
    final_list = [rank_stock_list['code'][totalcount[-1 - i][0]] for i in range(min(g.sellrank, len(rank_stock_list)))]
    stock_list = final_list
    return stock_list
```

### 2.7 辅助函数

这些辅助函数用于获取收盘价、计算股票涨幅、过滤停牌股票等。

```python
# 获取收盘价
def get_close_price(code, n, unit='
1d'):
    return attribute_history(code, n, unit, 'close')['close'][0]
# 获取增长率
def get_growth_rate(days, code):
    try:
        price_period = attribute_history(code, days, '1d', 'close', False)['close'][0]
        pricenow = get_close_price(code, 1, '1m')
        if not math.isnan(pricenow) and not math.isnan(price_period) and price_period != 0:
            return pricenow / price_period
        else:
            return 100
    except Exception as e:
        print(f"Error calculating growth rate for stock {code}: {e}")
        return 100
# 定义平仓，卖出指定持仓
def close_position(code):
    order = order_target_value(code, 0)
    if order is not None and order.status == OrderStatus.held:
        g.sold_stock = 0
```

# 3. 策略优化建议

  1. **动态调仓** ：在不同的市场环境中，可能需要动态调整持仓的频率和仓位。

  2. **增加风险控制** ：结合风险管理策略，如止损机制或仓位限制，以减少潜在的亏损。

  3. **因子优化** ：对因子权重进行调优，结合回测结果，进一步提升策略的表现。

通过该策略，投资者可以在多因子模型的基础上，构建出更优的股票组合，实现稳健的投资收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
