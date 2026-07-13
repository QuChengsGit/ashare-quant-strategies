# 65、回调买入与EMA筛选策略

### 策略介绍

**回调买入与EMA筛选策略** 是一种基于市场回调机会和技术分析的量化交易策略。该策略通过选择市场中近期表现强势的股票，并在出现回调后进行买入，同时结合指数移动平均线（EMA）作为辅助筛选条件，以期获得市场反弹中的收益。策略采用每日开盘后进行交易，持股周期为一天，通过过滤特定的股票以避免潜在风险。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
from jqdata import *
def initialize(context):
    log.set_level('order', 'warning')  # 设置日志级别
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 避免未来数据
    set_slippage(FixedSlippage(0.02))  # 固定滑点设置
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')  # 设置交易成本
    set_benchmark('399303.XSHE')  # 设置基准指数为中证500指数
    g.choice = 500  # 选择前500只股票
    g.stock_num = 5  # 最大持仓股票数量
    g.stock_pool = []  # 股票池
    run_daily(my_trade, time='9:30', reference_security='399303.XSHE')  # 每天9:30运行交易函数
```

技术说明：

  * **初始化函数** ：设置策略的基础配置，包括日志、滑点、交易成本和基准指数等。策略的交易时间设定为每日开盘后的9:30。

2\. 股票过滤与选股逻辑

```python
def filter_specials(context, stock_list):
    """
    过滤特定类型的股票：
    1. 涨停、跌停、停牌股票；
    2. ST、*ST、退市股票；
    3. 创业板、科创板股票；
    4. 次新股。
    """
    curr_data = get_current_data()
    stock_list = [stock for stock in stock_list if not (
        curr_data[stock].paused or  # 停牌
        curr_data[stock].is_st or  # ST股票
        ('ST' in curr_data[stock].name) or
        ('*' in curr_data[stock].name) or
        ('退' in curr_data[stock].name) or
        (stock.startswith('688'))  # 科创板股票
    )]
    return stock_list
def before_trading_start(context):
    # 获取市值前500的股票并过滤特定股票
    fundamentals_data = get_fundamentals(query(valuation.code, valuation.market_cap).order_by(valuation.market_cap.asc()).limit(g.choice))
    g.stock_pool = list(fundamentals_data['code'])
    g.stock_pool = filter_specials(context, g.stock_pool)
```

技术说明：

  * **股票过滤** ：在每日开盘前，筛选出符合条件的股票池。过滤掉ST、科创板、次新股以及停牌等高风险股票。

  * **市值筛选** ：策略选择市值排名前500的股票作为初始筛选的基础。

3\. 交易执行与动态调仓

```python
def my_trade(context):
    sell(context)
    buy(context)
def sell(context):
    # 卖出持仓中的所有股票
    for position in list(context.portfolio.positions.values()):
        if position.closeable_amount > 0:
            close_position(position)
def buy(context):
    data_today = get_current_data()
    position_count = len(context.portfolio.positions)
    # 选股逻辑：昨日收盘价大于5日均价，且今日开盘价低于昨日最低价
    buy_stocks = []
    for s in g.stock_pool:
        if position_count + len(buy_stocks) >= g.stock_num:
            break
        df = attribute_history(s, 5, '1d', ('close', 'low', 'high', 'paused'), False)
        if df['paused'].max() == 0:  # 过去5天没有停盘
            today_open = data_today[s].day_open
            prev_close = df['close'][-1]
            prev_low = df['low'][-1]
            chg = (today_open - prev_close) / prev_close * 100  # 计算开盘时跌幅
            if today_open < prev_low and -8 < chg < -1:
                low = min(df['low'].values[-4:])
                high = max(df['high'].values[-4:])
                precent = (high - low) / low * 100  # 计算4天振幅
                if precent <= 20:
                    df['ema'] = df['close'].ewm(span=5).mean()
                    ema = df['ema'].values[-1]
                    if prev_close > ema:
                        buy_stocks.append(s)
    # 按选股数分配资金买入
    target_num = len(buy_stocks)
    if target_num > 0:
        value = context.portfolio.available_cash / g.stock_num
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                open_position(stock, value)
```

技术说明：

  * **选股逻辑** ：基于昨日收盘价与5日均线的比较，并结合今日开盘价与昨日最低价的关系，筛选出符合条件的股票进行买入。

  * **资金分配** ：将资金均分至选出的股票中，确保每只股票的买入金额相同。

4\. 交易模块与风险控制

```python
# 交易模块-自定义下单
def order_target_value_(security, value):
    if value == 0:
        log.debug("Selling out %s" % security)
    else:
        log.debug("Order %s to value %f" % (security, value))
    return order_target_value(security, value)
# 交易模块-开仓
def open_position(security, value):
    print("buy:" + security + " " + str(value))
    _order = order_target_value_(security, value)
    if _order is not None and _order.filled > 0:
        return True
    return False
# 交易模块-平仓
def close_position(position):
    security = position.security
    _order = order_target_value_(security, 0)
    if _order is not None:
        if _order.status == OrderStatus.held and _order.filled == _order.amount:
            return True
    return False
```

技术说明：

  * **自定义下单函数** ：实现开仓和平仓操作，确保每次交易的执行逻辑清晰，并通过日志记录交易信息。

  * **风险控制** ：每日持有的股票在第二天无条件卖出，降低持仓风险。

### 策略优势

  * **回调买入策略** ：利用市场短期回调后的反弹机会，通过技术指标筛选出潜在的投资机会。

  * **简单有效** ：策略逻辑清晰，能够有效避免高风险股票，适合于震荡市场环境下的短线交易。

  * **资金均衡分配** ：确保每次交易中持仓股票的资金分配均衡，减少单一股票波动对整体组合的影响。

### 总结

**回调买入与EMA筛选策略** 结合了回调买入与技术指标筛选的策略特点，通过过滤特定类型的股票并在市场回调时寻找买入机会。该策略适用于震荡市场中追求短期收益的投资者。策略逻辑简单易懂，执行效率高，在控制风险的同时，能有效捕捉市场中的短线机会。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
