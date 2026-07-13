# 80、高效多因子选股策略

# 策略概述

**高效多因子选股策略** 是一种基于多因子选股模型的量化投资策略。策略通过综合考虑市值、流通市值、价格、成交量及涨幅等因素，筛选出具有潜力的股票组合，并结合涨停、跌停、ST、次新股等过滤条件，进行动态调整持仓。策略旨在通过严密的选股和风险管理，实现稳健的投资回报。

### 各部分功能代码与详细说明

1\. 初始化函数 (initialize)

```python
def initialize(context):
    # 设定基准
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 设置滑点为理想情况
    set_slippage(PriceRelatedSlippage(0.00))
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5),type='stock')
    # 初始化全局变量
    g.stock_num = 50  # 最大持仓数量
    g.high_limit_list = []  # 昨日涨停股票列表
    g.hold_list = []  # 当前持仓股票列表
    g.weights = [1.0, 1.0, 1.6, 0.8, 2.0]  # 因子权重
    g.black_list = []  # 风险黑名单
    # 设置定时任务
    run_daily(prepare_stock_list, '9:05')
    run_daily(get_black_list, '9:05')  # 获取风险黑名单
    run_weekly(adjust_position, 1, '09:30')
    run_daily(check_limit_up, '14:00')
```

  * **功能说明** : 初始化策略时，设置了交易基准、滑点、交易成本等参数，定义了策略中的全局变量，并设置了每日和每周的定时任务。

  * **关键参数** :

    * g.stock_num: 最大持仓数量。

    * g.weights: 用于计算合成因子的权重。

2\. 准备股票池 (prepare_stock_list)

```python
def prepare_stock_list(context):
    # 获取已持有列表
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    # 获取昨日涨停列表
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.high_limit_list = list(df.code)
    else:
        g.high_limit_list = []
```

  * **功能说明** : 准备当前持仓股票列表，并筛选出昨日涨停的股票。

  * **关键逻辑** :

    * 使用 get_price 获取昨日涨停股票列表，方便后续进行特别处理。

3\. 获取黑名单 (get_black_list)

```python
def get_black_list(context):
    # 检查当前时间是否在特定日期范围内
    def today_is_between(context, start_date, end_date):
        today = context.current_dt.strftime('%m-%d')
        return start_date <= today <= end_date
    # 获取黑名单股票列表
    def predict_st_stocks(stock_list, stat_date, fqd):
        tmp = []
        for stock in stock_list:
            try:
                df = get_history_fundamentals(stock, fields=[income.net_profit, indicator.adjusted_profit], watch_date=stat_date, count=11, interval='1q')
                df = df.set_index('statDate')
                y1 = sum(df.loc[fqd[0]][income.net_profit])
                y2 = sum(df.loc[fqd[1]][income.net_profit])
                y3 = sum(df.loc[fqd[2]][income.net_profit])
                if min(y1, y2, y3) < 0:
                    tmp.append(stock)
            except:
                pass
        return tmp
    # 获取黑名单股票
    if today_is_between(context, '11-01', '12-31'):
        sd = context.current_dt.strftime('%Y-%m-%d')[:4] + '-11-01'
        df = get_all_securities(types=['stock'], date=sd)
        stock_list = list(df.index)
        stock_list = filter_kcbj_stock(stock_list)
        stock_list = filter_new_stock(context, stock_list, 500)
        fiscal_quarter_date_list = get_fiscal_quarters(sd)
        g.black_list = predict_st_stocks(stock_list, sd, fiscal_quarter_date_list)
```

  * **功能说明** : 根据上市公司的财务状况预测可能进入黑名单的股票，主要针对ST风险进行预测。

  * **关键逻辑** :

    * 检查公司净利润连续亏损的情况，预测哪些股票可能会被ST，并将其加入黑名单。

4\. 选股模块 (get_stock_list)

```python
def get_stock_list(context):
    # 获得初始列表
    yesterday = context.previous_date
    initial_list = get_all_securities('stock', yesterday).index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_new_stock(context, initial_list, 375)
    initial_list = filter_st_stock(initial_list)
    q = query(
        valuation.code, valuation.market_cap, valuation.circulating_market_cap
    ).filter(
        valuation.code.in_(initial_list),
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0
    ).order_by(
        valuation.market_cap.asc()).limit(100)
    df = get_fundamentals(q, date=yesterday)
    df.index = df.code
    # 计算合成因子并排序
    df['score'] = df.apply(lambda row: sum([
        g.weights[0] * math.log(df['market_cap'].min() / row['market_cap']),
        g.weights[1] * math.log(df['circulating_market_cap'].min() / row['circulating_market_cap']),
        g.weights[2] * math.log(df['price_now'].min() / row['price_now']),
        g.weights[3] * math.log(df['total_volume_n'].min() / row['total_volume_n']),
        g.weights[4] * math.log(df['m_days_return'].min() / row['m_days_return'])
    ]), axis=1)
    df = df.sort_values(by='score', ascending=False)
    final_list = list(df.index)
    return final_list
```

  * **功能说明** : 根据多因子模型筛选股票，最终返回得分最高的股票列表。

  * **关键逻辑** :

    * 计算合成因子：综合市值、流通市值、价格、成交量和涨幅等因素，并按得分排序。

5\. 调整持仓 (adjust_position)

```python
def adjust_position(context):
    # 获取应买入列表
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    target_list = target_list[:min(g.stock_num, len(target_list))]
    # 排除黑名单股票
    target_list = [stock for stock in target_list if stock not in g.black_list]
    # 调仓卖出
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
            position = context.portfolio.positions[stock]
            close_position(position)
    # 调仓买入
    for stock in target_list:
        if context.portfolio.positions[stock].total_amount == 0:
            value = context.portfolio.cash / (len(target_list) - len(context.portfolio.positions))
            open_position(stock, value)
```

  * **功能说明** : 根据筛选出的股票列表调整当前持仓，卖出不符合条件的股票，并买入新的目标股票。

  * **关键逻辑** :

    * 在调仓时排除涨停股票和黑名单股票，保证持仓的安全性和流动性。

6\. 检查涨停股票 (check_limit_up)

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close','high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0,0] < current_data.iloc[0,1]:
                position = context.portfolio.positions[stock]
                close_position(position)
```

  * **功能说明** : 检查昨日涨停的股票，如果今日涨停打开则卖出该股票。

  * **关键逻辑** :

  * 防止涨停打开后股价下跌，通过及时卖出减少损失。

7\. 交易模块 (order_target_value_, open_position, close_position)

```python
def order_target_value_(security, value):
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    order = order_target_value_(position.security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
```

  * **功能说明** : 定义了开仓、平仓的交易逻辑，通过封装函数简化代码，统一管理交易指令。

### 总结

**高效多因子选股策略** 结合了多因子模型的优势，通过多维度因子筛选出潜力股票，并在严格的风险管理机制下进行动态调仓，实现了稳健的投资回报。这种策略适合对市场有一定了解的投资者，尤其是希望通过多因子分析来获取超额收益的量化交易员。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
