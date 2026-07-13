# 85、因子选股与风险控制策略

# 策略概述

**因子选股与风险控制策略** 是一种基于基本面因子选股，并结合多种风险控制手段来优化持仓的量化投资策略。该策略在每周初通过基本面因子筛选股票，应用多种过滤条件剔除不符合标准的股票，并最终构建一个多因子优化的股票组合。策略在周一开盘时执行交易，并在日常操作中结合复盘信息，保持仓位的优化和风险控制。

# 策略详细介绍

  1. **策略思想** ：

     * 策略基于基本面因子（如销售增长率、每股收益等）筛选出具备增长潜力的股票。

     * 应用多种风险控制手段（如剔除 ST 股、停牌股、涨停跌停股）过滤掉高风险股票。

     * 每周初筛选股票并根据仓位配置分布进行调仓，确保持仓数量与风险控制一致。

  2. **关键要素** ：

     * **因子选股** ：通过销售增长率等因子筛选出一批基本面优良的股票。

     * **风险过滤** ：过滤掉新股、ST股、科创板、涨跌停及停牌股票，以降低交易风险。

     * **持仓调仓** ：每周初根据筛选结果调整持仓，保持股票组合的优化。

# 策略代码与功能说明

1\. 初始化函数与全局变量设置 (initialize)

```python
def initialize(context):
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')
    # 选股参数
    g.stock_num = 5  # 持仓数
    # 设置交易时间，每周一运行
    run_weekly(print_stock_list_before_open, weekday=1, time='9:15', reference_security='000300.XSHG')
    run_weekly(my_trade, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
```

  * **功能说明** : 初始化策略参数，包括基准设置、交易成本、持仓数量等，并设定每周一的交易逻辑。

  * **关键逻辑** :

    * set_benchmark 设置策略的基准指数为中证 500 指数（000905.XSHG）。

    * run_weekly 和 run_daily 设定了每周一进行选股交易，并在每日收盘后打印持仓信息。

2\. 因子筛选与股票列表生成 (get_factor_filter_list)

```python
def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame(columns=['code','score'])
    df['code'] = stock_list
    df['score'] = score_list
    df = df.dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    filter_list = list(df.code)[int(p1*len(stock_list)):int(p2*len(stock_list))]
    return filter_list
```

  * **功能说明** : 根据指定因子对股票进行筛选和排序，返回符合要求的股票列表。

  * **关键逻辑** :

    * get_factor_values 获取股票的因子值，如销售增长率等。

    * 对股票进行排序并根据百分位 p1 和 p2 提取股票列表。

3\. 股票列表生成与筛选 (get_stock_list)

```python
def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    x_list = get_factor_filter_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(x_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    df = df[df['eps'] > 0]
    final_list = list(df.code)
    return final_list
```

  * **功能说明** : 生成初步股票池并经过多层筛选，最终返回符合因子要求的股票列表。

  * **关键逻辑** :

    * 依次过滤新股、科创板股票、ST股票。

    * 根据销售增长率和流通市值筛选出最终的股票池。

4\. 股票筛选前打印自选股列表 (print_stock_list_before_open)

```python
def print_stock_list_before_open(context):
    stock_list = get_stock_list(context)
    stock_list = filter_paused_stock(stock_list)
    stock_list = stock_list[:g.stock_num]
    print('今日自选股:{}'.format(stock_list))
```

  * **功能说明** : 在开盘前打印筛选出的自选股列表，以便了解当日的备选股票。

  * **关键逻辑** :

    * 打印最终筛选出的股票列表，确保在开盘前对交易目标有清晰了解。

5\. 多层风险过滤 (filter_*)

```python
# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
# 过滤ST及退市股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
# 过滤涨停股票
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] < current_data[stock].high_limit]
# 过滤跌停股票
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or last_prices[stock][-1] > current_data[stock].low_limit]
# 过滤科创板股票
def filter_kcb_stock(context, stock_list):
    return [stock for stock in stock_list if stock[0:3] != '688']
# 过滤次新股
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [stock for stock in stock_list if not yesterday - get_security_info(stock).start_date < datetime.timedelta(days=250)]
```

  * **功能说明** : 多层过滤机制分别针对停牌、ST、涨停、跌停、科创板和次新股进行过滤，确保选出的股票符合交易条件。

  * **关键逻辑** :

    * 每个过滤模块分别执行特定条件的过滤，最后保留符合所有条件的股票。

6\. 调仓与交易模块 (adjust_position, my_trade)

```python
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            log.info("[%s]不在应买入列表中" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("[%s]已经持有无需重复买入" % (stock))
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        break
def my_trade(context):
    check_out_list = get_stock_list(context)
    check_out_list = filter_limitup_stock(context, check_out_list)
    check_out_list = filter_limitdown_stock(context, check_out_list)
    check_out_list = filter_paused_stock(check_out_list)
    check_out_list = check_out_list[:g.stock_num]
    adjust_position(context, check_out_list)
```

  * **功能说明** : 根据筛选出的股票列表

进行调仓，卖出不符合条件的股票，买入符合条件的股票。

  * **关键逻辑** :

    * adjust_position 根据当前持仓和筛选结果进行调仓，确保持仓符合策略要求。

7\. 持仓信息打印模块 (print_position_info)

```python
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：' + str(_trade))
    for position in list(context.portfolio.positions.values()):
        securities = position.security
        cost = position.avg_cost
        price = position.price
        ret = 100 * (price / cost - 1)
        value = position.value
        amount = position.total_amount
        print('代码:{}'.format(securities))
        print('成本价:{}'.format(format(cost,'.2f')))
        print('现价:{}'.format(price))
        print('收益率:{}%'.format(format(ret,'.2f')))
        print('持仓(股):{}'.format(amount))
        print('市值:{}'.format(format(value,'.2f')))
        print('———————————————————————————————————')
    print('———————————————————————————————————————分割线————————————————————————————————————————')
```

  * **功能说明** : 每日打印持仓和交易信息，便于复盘和策略调整。

  * **关键逻辑** :

    * 打印持仓股票的详细信息，包括成本价、现价、收益率等。

### 总结

**因子选股与风险控制策略** 通过对基本面因子的筛选和多层次的风险过滤，构建一个优质且风险可控的股票组合。策略在每周初进行调仓，确保持仓符合最新的选股标准。该策略适合希望通过基本面分析并结合多层风险控制来优化股票组合的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
