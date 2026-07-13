# 111、多因子成长价值轮动策略（源码解析和下载）

通过结合成长因子与价值因子在A股市场中进行股票精选与动态调仓。策略首先筛选营业收入增长率、利润总额增长率和五年盈利增长率表现优异的成长股，再结合市值和EPS进行价值过滤，同时剔除新股、科创板、ST及停牌、涨跌停股票，以降低流动性和财务风险。每周一开盘调仓，最多持有5只股票，资金平均分配，确保仓位均衡；每日收盘打印持仓和成交信息，便于监控。策略在每年再平衡期（4月5日-4月30日）进行清仓，降低年度集中持仓风险。回测中采用真实价格、无滑点、避免未来函数偏差，并设置合理交易成本。整体策略兼顾成长性与价值性，通过严格风控、动态调仓和资金均分实现稳健收益与风险控制。**本文策略的完整代码下载地址请见文末最下方。**

  1. **策略目标** ：在A股市场中，通过结合成长因子与价值因子，动态挑选高质量股票，实现稳健收益与控制回撤。

  2. **核心思想** ：

     * 利用 **成长因子** （营业收入增长率、利润总额增长率、五年盈利增长率）选出成长优选股票池。

     * 结合 **价值因子** （市值和EPS）进行二次筛选，剔除高估值或财务异常股票。

     * 避免投资新股、ST股、科创板股票、涨跌停和停牌股票，以降低流动性和交易风险。

  3. **交易逻辑** ：

     * 每周一开盘时进行调仓（选股并调整持仓），每日收盘打印持仓信息。

     * 再平衡期（每年4月5日-4月30日）清仓，以降低年度集中持仓风险。

     * 最大持仓数量为5只，资金平均分配。

  4. **风控与回测设置** ：

     * 使用真实价格回测，避免滑点和未来函数偏差。

     * 设置合理交易成本和最低佣金。

## 二、策略功能模块与代码说明

下面按功能模块逐条解析每行代码功能及逻辑：

### 1. 初始化函数 initialize(context)

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设置策略基准指数为中证500
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来函数数据偏差
    set_slippage(FixedSlippage(0))  # 设置滑点为0
```

  * **说明** ：保证回测价格真实，避免未来数据泄露。

```python
    set_order_cost(
        OrderCost(
            open_tax=0,
            close_tax=0.001,
            open_commission=0.0003,
            close_commission=0.0003,
            close_today_commission=0,
            min_commission=5
        ),
        type='fund'
    )
```

  * **说明** ：设置交易成本（佣金+印花税），确保回测成本接近实际交易成本。

```python
    log.set_level('order', 'error')  # 仅打印错误日志
```

  * **说明** ：减少回测输出冗余信息，仅关注重要错误。

```python
    g.stock_num = 5  # 最大持仓股票数
    g.no_trading_today_signal = False  # 是否禁止交易标识
    g.hold_list = []  # 当前持仓列表
```

  * **说明** ：定义全局策略参数。

```python
    run_weekly(my_trade, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(close_account, '14:30')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

  * **说明** ：设置交易调度：

    * 每周一开盘9:30运行调仓。

    * 每日14:30检查再平衡期是否清仓。

    * 每日收盘前打印持仓信息。



### 2. 选股模块

2.1 获取股票列表 get_stock_list(context)

```python
def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = get_all_securities().index.tolist()  # 获取所有股票
```

  * **说明** ：获取市场中所有股票代码。

```python
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
```

  * **说明** ：剔除上市不足250天新股、科创板股票及ST/退市股票。

```python
    factor_values = get_factor_values(
        initial_list,
        ['operating_revenue_growth_rate', 'total_profit_growth_rate', 'earnings_growth'],
        end_date=yesterday,
        count=1
    )
```

  * **说明** ：获取成长因子数据（营业收入、利润增长、五年盈利增长）。

```python
    df = pd.DataFrame(index=initial_list)
    df['operating_revenue_growth_rate'] = list(factor_values['operating_revenue_growth_rate'].T.iloc[:,0])
    df['total_profit_growth_rate'] = list(factor_values['total_profit_growth_rate'].T.iloc[:,0])
    df['earnings_growth'] = list(factor_values['earnings_growth'].T.iloc[:,0])
```

  * **说明** ：将因子数据整理为 DataFrame，便于计算综合评分。

```python
    df['total_score'] = 0.2*df['operating_revenue_growth_rate'] + 0.4*df['total_profit_growth_rate'] + 0.4*df['earnings_growth']
```

  * **说明** ：计算综合评分，总评分权重：收入20%、利润40%、盈利40%。

```python
    df = df.sort_values(by='total_score', ascending=False)
    complex_growth_list = list(df.index)[:max(int(0.1*len(df)),1)]
```

  * **说明** ：选出前10%成长优选股票池。

```python
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps)\
        .filter(valuation.code.in_(complex_growth_list))\
        .order_by(valuation.circulating_market_cap.asc())
    df_final = get_fundamentals(q)
    df_final = df_final[df_final['eps']>0]
    return list(df_final.code)
```

  * **说明** ：按市值升序、EPS>0筛选股票，得到最终可交易股票列表。



2.2 打印开盘自选股 print_stock_list_before_open(context)

```python
def print_stock_list_before_open(context):
    stock_list = get_stock_list(context)
    stock_list = filter_paused_stock(stock_list)
    stock_list = stock_list[:g.stock_num]
    print('今日自选股:{}'.format(stock_list))
```

  * **说明** ：开盘前打印可交易股票，便于人工观察和调试。



### 3. 交易模块

3.1 开盘调仓 my_trade(context)

```python
def my_trade(context):
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')
    g.hold_list = list(context.portfolio.positions.keys())
    if g.no_trading_today_signal: return
```

  * **说明** ：判断再平衡期，禁止交易。

```python
    check_out_list = get_stock_list(context)
    check_out_list = filter_limitup_stock(context, check_out_list)
    check_out_list = filter_limitdown_stock(context, check_out_list)
    check_out_list = filter_paused_stock(check_out_list)
    check_out_list = check_out_list[:g.stock_num]
```

  * **说明** ：筛选可交易股票（过滤涨停、跌停、停牌），取前N只。

```python
    adjust_position(context, check_out_list)
```

  * **说明** ：调整仓位买卖操作。



3.2 仓位调整 adjust_position(context, buy_stocks)

```python
def adjust_position(context, buy_stocks):
    for stock in list(context.portfolio.positions.keys()):
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
```

  * **说明** ：卖出不在买入列表的持仓。

```python
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                open_position(stock, value)
                if len(context.portfolio.positions) >= g.stock_num: break
```

  * **说明** ：平均分配资金买入缺仓股票，确保最大持仓不超过5只。



3.3 买入/卖出封装

```python
def order_target_value_(security, value):
    if value == 0: log.debug("Selling out %s" % security)
    else: log.debug("Order %s to value %f" % (security, value))
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    return order is not None
```

  * **说明** ：封装交易操作并打印调试信息。

3.4 再平衡期清仓 close_account(context)

```python
def close_account(context):
    if g.no_trading_today_signal and g.hold_list:
        for stock in g.hold_list:
            order_target_value(stock, 0)
            log.info("卖出[%s]" % stock)
```

  * **说明** ：再平衡期间全部清仓，控制年度集中持仓风险。

### 4. 过滤函数

```python
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [s for s in stock_list if not current_data[s].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [s for s in stock_list if not current_data[s].is_st and 'ST' not in current_data[s].name and '*' not in current_data[s].name and '退' not in current_data[s].name]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [s for s in stock_list if s in context.portfolio.positions or last_prices[s][-1] < current_data[s].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [s for s in stock_list if s in context.portfolio.positions or last_prices[s][-1] > current_data[s].low_limit]
def filter_kcb_stock(context, stock_list): return [s for s in stock_list if not s.startswith('688')]
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [s for s in stock_list if (yesterday - get_security_info(s).start_date).days >= 250]
def today_is_between(context, start_date, end_date):
    today = context.current_dt.strftime('%m-%d')
    return start_date <= today <= end_date
```

  * **说明** ：停牌/ST股/新股/科创板/涨跌停股票过滤，并判断再平衡日期。

### 5. 持仓信息打印 print_position_info(context)

```python
def print_position_info(context):
    trades = get_trades()
    for t in trades.values(): print('成交记录：'+str(t))
    for pos in context.portfolio.positions.values():
        sec = pos.security
        cost = pos.avg_cost
        price = pos.price
        ret = 100*(price/cost-1)
        value = pos.value
        amount = pos.total_amount
        print(f'代码:{sec}, 成本价:{cost:.2f}, 现价:{price:.2f}, 收益率:{ret:.2f}%, 持仓(股):{amount}, 市值:{value:.2f}')
```

  * **说明** ：打印每日成交记录和持仓明细，便于策略监控和分析。

## 三、策略总结

  1. **选股逻辑** ：

     * 成长因子评分：营业收入、利润、盈利增长。

     * 价值过滤：EPS>0、小市值优先。

     * 风控过滤：停牌、新股、科创板、ST、涨跌停。

  2. **交易逻辑** ：

     * 每周一调仓，最大持仓5只，资金平均分配。

     * 再平衡期清仓，降低集中持仓风险。

  3. **回测设置** ：

     * 使用真实价格、无滑点、避免未来函数。

     * 设置交易成本、最低佣金。

  4. **风控特点** ：

     * 股票选择严格过滤风险股。

     * 持仓均衡、动态调仓，降低回撤。

**策略特点** ：

  * 成长+价值多因子选股，兼顾收益和稳健性。

  * 动态调仓、资金均分，降低个股风险。

  * 风控严格，避免高风险股票和交易异常。

  * 回测设置真实，便于实际交易落地。



**通过网盘分享的文件：111、A股多因子成长价值轮动策略.txt.zip**

**链接: https://pan.baidu.com/s/17w3li17WqBOZ909NMeVq4w 提取码: 1mvw**

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
