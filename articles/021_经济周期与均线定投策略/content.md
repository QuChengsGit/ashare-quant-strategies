# 21、经济周期与均线定投策略

**1\. 初始化函数 (initialize)**

功能说明:

  * 设定策略的基准、模式、初始参数、手续费、以及定时函数。

  * 初始化参数包括策略模式、记录点位、加仓次数、下单基数、债券和股票安全代码、过热状态标志、年均线值等。

代码:

```python
def initialize(context):
    g.mode = 0
    g.record = 0.0
    g.times = -1
    g.order_amount = 0.04
    g.begin_date = '2013-01'
    g.stock_security = '510300.XSHG'
    g.bond_security = '511010.XSHG'
    g.over_hot = False
    g.yearMa10 = 0.0
    set_benchmark('000300.XSHG')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    run_daily(handle, time='14:55')
```

2\. **交易处理函数 (handle)**

功能说明:

  * **经济周期定投** :

    * 判断PMI数据是否满足买入条件。

    * 根据供需格局和库存格局决定是否进入长线玩法。

    * 执行买入操作，并记录买入时的指数点位。

  * **年均线定投** :

    * 判断沪深300指数是否跌破年均线的MA10。

    * 根据跌破情况决定是否进入中线玩法，并记录买入时的MA10值。

  * **右侧买入** :

    * 计算短期均线情况，判断是否满足全仓买入股票的条件。

  * **止盈操作** :

    * 根据当前模式和市场情况，决定是否卖出股票，转换为债券。

代码:

```python
def handle(context):
    pre_date = context.previous_date
    current_date = context.current_dt.strftime('%Y-%m-%d').split('-')
    current_date = datetime.date(int(current_date[0]), int(current_date[1]), int(current_date[2]))
    diff_days = (current_date - pre_date).days
    if g.mode in [0, 2]:
        current_date = current_date.strftime('%Y-%m')
        x = [0,1,2,3,4,5,6,7,8,9,10,11,12]
        y = get_PMI(current_date)
        params = op.curve_fit(func, x, y)
        k = 2 * params[0][0] * 12 + params[0][1]
        if k > 0.0 and y[-1] >= 50.0 and y[0] <= y[-1]:
            provide_and_need = calc_provide_and_need(g.begin_date, current_date)
            if provide_and_need[0] < 50.0 and provide_and_need[1] > 50.0:
                save = calc_save(g.begin_date, current_date)
                if save[0] < 50.0:
                    g.mode = 1
    if g.mode == 1:
        if g.times == -1:
            g.record = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
        if g.bond_security in context.portfolio.positions.keys():
            order_target(g.bond_security, 0)
        current_price = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
        fund_price = float(np.array(get_bars(g.stock_security, 1, '1d', fields=['close'], include_now=True, df=True))[0])
        withdraw = Decimal(str(current_price)) / Decimal(str(g.record)) - Decimal('1.0')
        if withdraw < Decimal('-0.02') or g.times == -1:
            g.times += 1
            order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
            g.record = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
        else:
            if diff_days > 2:
                order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
    if g.mode in [0, 2]:
        if g.mode == 0:
            year_point = change_to_yeak_k()
            yearMa10 = year_move_average(year_point)
            current_price = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
            fund_price = float(np.array(get_bars(g.stock_security, 1, '1d', fields=['close'], include_now=True, df=True))[0])
            if current_price < yearMa10:
                g.mode = 2
                g.record = yearMa10
                g.times += 1
                if g.bond_security in context.portfolio.positions.keys():
                    order_target(g.bond_security, 0)
                order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
        if g.mode == 2:
            current_price = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
            fund_price = float(np.array(get_bars(g.stock_security, 1, '1d', fields=['close'], include_now=True, df=True))[0])
            withdraw = Decimal(str(current_price)) / Decimal(str(g.record)) - Decimal('1.0')
            if withdraw < Decimal('-0.05'):
                g.times += 1
                order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
                g.record = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
            else:
                if diff_days > 2:
                    order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
    if g.mode in [1, 2]:
        ma5 = day_move_average(5, True)
        ma10 = day_move_average(10, True)
        ma20 = day_move_average(20, True)
        ma30 = day_move_average(30, True)
        ma30_pre = day_move_average(30, False)
        if ma5 > ma10 > ma20 > ma30 > ma30_pre:
            order_value(g.stock_security, context.portfolio.available_cash)
    if g.stock_security in context.portfolio.positions.keys():
        sell_stock_security(current_date, context.portfolio.total_value, list(context.portfolio.positions.keys()))
```

3\. **功能函数**

**获取PMI函数 (get_PMI)**

获取过去十三个月PMI数据的值。

```python
def get_PMI(date: str) -> list:
    start_date = date
    for i in range(13):
        start_date = calc_last_month(start_date)
    df = macro.run_query(query(
        macro.MAC_MANUFACTURING_PMI.pmi
    ).filter(
        macro.MAC_MANUFACTURING_PMI.stat_month >= start_date,
        macro.MAC_MANUFACTURING_PMI.stat_month < date
    ).order_by(
        macro.MAC_MANUFACTURING_PMI.stat_month.asc()
    ))
    return list(np.array(df['pmi']))
```

**计算供需格局 (calc_provide_and_need)**

返回生产指数和新订单指数的百分位。

```python
def calc_provide_and_need(start_date: str, end_date: str) -> tuple:
    end_date = calc_last_month(end_date)
    df = macro.run_query(query(
        macro.MAC_MANUFACTURING_PMI.stat_month,
        macro.MAC_MANUFACTURING_PMI.produce_idx,
        macro.MAC_MANUFACTURING_PMI.new_orders_idx
    ).filter(
        macro.MAC_MANUFACTURING_PMI.stat_month >= start_date,
        macro.MAC_MANUFACTURING_PMI.stat_month <= end_date
    ).order_by(
        macro.MAC_MANUFACTURING_PMI.stat_month.desc()
    ))
    produce_seq = np.array(df['produce_idx'])
    new_orders_seq = np.array(df['new_orders_idx'])
    produce_percent = percentile(produce_seq, df.iloc[0, 1])
    new_orders_percent = percentile(new_orders_seq, df.iloc[0, 2])
    return (produce_percent, new_orders_percent)
```

**计算库存格局 (calc_save)**

返回原材料和产成品库存指数的百分位。

```python
def calc_save(start_date: str, end_date: str) -> tuple:
    end_date = calc_last_month(end_date)
    df = macro.run_query(query(
        macro.MAC_MANUFACTURING_PMI.stat_month,
        macro.MAC_MANUFACTURING_PMI.raw_material_idx,
        macro.MAC_MANUFACTURING_PMI.finished_produce_idx
    ).filter(
        macro.MAC_MANUFACTURING_PMI.stat_month >= start_date,
        macro.MAC_MANUFACTURING_PMI.stat_month <= end_date
    ).order_by(
        macro.MAC_MANUFACTURING
_PMI.stat_month.desc()
    ))
    raw_material_seq = np.array(df['raw_material_idx'])
    finished_produce_seq = np.array(df['finished_produce_idx'])
    raw_material_percent = percentile(raw_material_seq, df.iloc[0, 1])
    finished_produce_percent = percentile(finished_produce_seq, df.iloc[0, 2])
    return (raw_material_percent, finished_produce_percent)
```

**获取年均线点位 (change_to_yeak_k)**

获取年均线点位。

```python
def change_to_yeak_k() -> list:
    date = get_previous_date('2015-01', '1m')
    result = []
    while date <= get_current_date():
        df = get_bars('000300.XSHG', 1, date, fields=['close'], include_now=True, df=True)
        df = df.rename(columns={'close': date})
        result.append(float(df[date].mean()))
        date = get_previous_date(date, '1m')
    return result
```

**年均线移动平均 (year_move_average)**

获取年均线移动平均值。

```python
def year_move_average(year_point: list) -> float:
    year_len = len(year_point)
    if year_len >= 2:
        x = np.arange(year_len)
        params = np.polyfit(x, year_point, 1)
        return params[0] * x[-1] + params[1]
    return year_point[0]
```

**日均线计算 (day_move_average)**

获取短期均线值。

```python
def day_move_average(day: int, is_today: bool) -> float:
    df = get_bars(g.stock_security, day, '1d', fields=['close'], include_now=is_today, df=True)
    return np.mean(df['close'])
```

**订单执行 (order_func 和 order_value)**

执行订单的核心函数。

```python
def order_func(total_value: float, available_cash: float, fund_price: float):
    order_amount = min(available_cash / fund_price, total_value * g.order_amount)
    order_target_value(g.stock_security, order_amount)
def order_value(stock: str, cash: float):
    order_amount = min(cash, 0.1 * context.portfolio.total_value)
    order_target_value(stock, order_amount)
```

**卖出操作 (sell_stock_security)**

根据当前模式执行卖出操作。

```python
def sell_stock_security(date: str, total_value: float, stocks: list):
    for stock in stocks:
        order_target(stock, 0)
    if g.mode == 1:
        g.mode = 0
    elif g.mode == 2:
        g.mode = 0
    elif g.mode == 0:
        g.mode = 2
```

### 说明

此策略根据经济周期和年均线移动平均来进行股票和债券的投资决策。每个功能函数都有明确的职责，如获取PMI数据、计算库存格局、执行买卖订单等。策略通过判断当前市场条件来决定买入和卖出的时机，并根据历史数据和市场走势来调整投资组合。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
