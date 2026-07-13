# 107、动量-均线止损与动态止盈策略

本策略结合动量因子与均线止损规则，形成了一种以动量为主、市场变化为辅的动态交易策略。其通过BOLL指标对市场的短期波动进行预判，并利用动态止损和止盈机制对股票持仓进行管理，从而确保在强势市场中保持盈利，在市场逆转时及时止损。具体来说，策略核心是通过动量因子选择股票，结合BOLL指标与均线进行动态止损，并以固定资金进行仓位调整，确保策略的平稳性和可操作性。**完整代码下载地址请见文末。**



### 1. **初始化函数 (initialize)**

该函数主要负责设置策略的基准、价格设置、交易成本、滑点等，同时安排每日的运行任务。

```python
def initialize(context):
    run_type = context.run_params.type
    log.info('开始 {} 交易.'.format(run_type))
    set_benchmark('000002.XSHG')  # 设置沪深300为基准
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 打开防未来数据选项
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.00012,\
                close_commission=0.0003, close_today_commission=0, min_commission=5),\
                type='fund')  # 设置交易费用
    log.set_level('order', 'error')  # 设置日志级别为error，减少不必要的信息输出
    g.strat_name = ''  # 策略名称，用于保存持仓列表
    g.yesterday_list = []  # 上一交易日持仓
    g.stock_list = []  # 今天的持股
    g.limit_price = [1, 100]  # 股价限制
    # 每日的定时任务
    run_daily(before_market_open, time='8:30', reference_security='000300.XSHG')
    run_daily(market_open, time='9:35', reference_security='000300.XSHG')
```

**说明** ：初始化函数主要负责设置交易环境和日常的任务安排，包括基准指数、滑点、费用、日志等，同时设定每日的任务调度（开盘前、开盘后等）。

### 2. **获取股票列表 (before_market_open)**

该函数在开盘前获取符合策略条件的股票池。

```python
def before_market_open(context):
    all_stock = set()
    # 使用BOLL策略筛选股票
    s1_stocks = Boll399101Strat().get_stock_list(context)
    all_stock.update(filter_price_stocks(context, s1_stocks, 20))
    g.stock_list = list(all_stock)  # 更新今天的持股列表
```

**说明** ：该函数调用了BOLL策略并对股票池进行过滤（如股价范围）。最终生成一个符合条件的股票列表，用于当天的交易。

### 3. **股价过滤 (filter_price_stocks)**

该函数根据股价范围过滤股票，确保交易的股票价格在设定范围内。

```python
def filter_price_stocks(context, stock_list, limit_count):
    min_price, max_price = g.limit_price[0], g.limit_price[1]
    new_list = []
    cur_data = get_current_data()
    for stock in stock_list:
        cur_price = cur_data[stock].last_price
        if (cur_price > max_price and stock not in context.portfolio.positions) \
            or cur_price < min_price:
            log.info(stock, cur_price, '超出限价范围', g.limit_price)
            continue
        new_list.append(stock)
        if len(new_list) >= limit_count:
            break
    return new_list[:limit_count]
```

**说明** ：通过获取每支股票的实时价格，并检查其是否在设定的最小和最大价格范围内。如果符合条件，则加入股票池。最多返回 limit_count 支股票。

### 4. **持仓检查与止损 (hold_check)**

该函数用于盘中检查持仓，并在符合条件时执行止损操作。

```python
def hold_check(context):
    N = 20
    for stk in context.portfolio.positions:
        stk_dict = context.portfolio.positions[stk]
        if stk_dict.closeable_amount == 0:
            continue
        dt = attribute_history(stk, N+2, '60m', ['close'])
        dt['man'] = dt.close / dt.close.rolling(N).mean()
        if dt.man[-1] >= 1.0:
            continue
        log.info("盘中止损，卖出：{}".format(stk))
        close_position(stk_dict)
```

**说明** ：检查每支持仓股票的价格变化情况，若其60分钟周期的价格跌破20日均线，则触发止损卖出。

### 5. **开盘后的仓位调整 (market_open)**

该函数在市场开盘后，根据选定的股票进行仓位调整。

```python
def market_open(context):
    print('入选股票:{}'.format(g.stock_list))
    adjust_position(context, g.stock_list)
```

**说明** ：在市场开盘后，策略将基于今天的选股结果，调用 adjust_position 函数进行仓位调整。

### 6. **开仓买入 (open_position)**

该函数负责执行开仓操作，买入股票。

```python
def open_position(security, value):
    order = order_target_value_(security, value)
    if order != None and order.filled > 0:
        return True
    return False
```

**说明** ：执行买入操作，根据给定的价值下单，如果成功成交，返回 True。

### 7. **平仓卖出 (close_position)**

该函数负责执行平仓操作，卖出股票。

```python
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0)
    if order != None:
        if order.status == OrderStatus.held and order.filled == order.amount:
            return True
    return False
```

**说明** ：执行卖出操作，卖出股票时，如果订单状态为 held 且成交量与委托量一致，则认为卖出成功。

### 8. **仓位调整 (adjust_position)**

该函数根据选股结果调整仓位，确保资金分配合理。

```python
def adjust_position(context, buy_stocks):
    # 清仓不在的股票
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)
    # 平均分配资金
    position_count = len(context.portfolio.positions)
    if len(buy_stocks) <= position_count:
        return
    value = int(context.portfolio.cash / (len(buy_stocks) - position_count))
    value = min(value, g.max_cash)
    value = int(int(value / 100) * 100)  # 按100取整
    for stock in buy_stocks:
        if get_pos_amount(context, stock) != 0:
            continue
        data = attribute_history(stock, 1, '1m', ['close']).close
        if value / data[0] < 110:
            continue
        open_position(stock, value)
        if len(context.portfolio.positions) >= len(buy_stocks):
            break
```

**说明** ：对已有的仓位进行清仓，同时根据剩余现金平均分配资金，并购买新的股票。

### 9. **下单交易 (order_target_value_)**

该函数用于生成交易订单。

```python
def order_target_value_(security, value):
    if value == 0:
        log.debug("卖出 %s" % (security))
    else:
        log.debug("调整 %s 市值到 %f" % (security, value))
    return order_target_value(security, value)
```

**说明** ：创建一个交易订单，调整目标市值。若目标市值为0，则为卖出操作。

### 10. **收盘后记录交易 (after_market_close)**

该函数用于记录当天的所有交易活动。

```python
def after_market_close(context):
    log.info(str('收盘后:' + str(context.current_dt.time())))
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：' + str(_trade))
    log.info('一天结束')
```

**说明** ：在市场收盘后，输出当天所有的交易记录，便于策略复盘。



### 总结：

本策略结合了动量因子和均线止损、动态止盈规则，通过BOLL指标筛选强势股票，并根据股票价格和技术指标进行仓位管理。该策略通过合理的止损止盈控制风险，确保在牛市中获取收益，在熊市中快速止损，灵活应对市场变化。

**完整代码下载地址链接:**[**https://pan.baidu.com/s/1Z-W14HAAyA4BvoMtXP7_EA**](<https://pan.baidu.com/s/1Z-W14HAAyA4BvoMtXP7_EA>)

**提取码: pymv**

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
