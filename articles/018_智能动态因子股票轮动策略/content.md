# 18、智能动态因子股票轮动策略

### 策略代码功能说明

下面是对策略的技术文档说明：

```python
import pandas as pd
def initialize(context):
    """
    初始化策略设置
    """
    log.set_level('order', 'error')  # 设置日志级别为错误
    set_option('use_real_price', True)  # 使用真实价格
    set_option('avoid_future_data', True)  # 避免使用未来数据
    g.days = 0  # 初始化运行天数
def after_code_changed(context):
    """
    更新策略配置，当代码更改时调用
    """
    unschedule_all()  # 取消所有已计划的事件
    run_daily(iUpdate, time='before_open')  # 每天开盘前更新股票池
    run_daily(iTrader, time='9:35')  # 每天9:35进行交易操作
    run_daily(iReport, time='after_close')  # 每天收盘后生成报告
def iUpdate(context):
    """
    更新股票池和持仓
    """
    nchoice = 120  # 股票池选择数量
    nposition = 100  # 最大持仓数量
    dt_last = context.previous_date  # 上一个交易日
    all_stock = get_all_securities('stock', dt_last)  # 获取所有股票
    cdata = get_current_data()  # 获取当前数据
    stocks = [s for s in all_stock.index if not cdata[s].is_st]  # 过滤ST股
    # 筛选市场资本小的股票，并按市场资本升序排序
    df = get_fundamentals(
        query(
            valuation.code,
            valuation.market_cap,
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,
        ).order_by(valuation.market_cap.asc()).limit(nchoice)
    ).dropna().set_index('code')
    g.choice = df.index.tolist()  # 更新选股列表
    g.position_size = 1.0 / nposition * context.portfolio.total_value  # 计算每个股票的持仓大小
def iTrader(context):
    """
    执行交易操作
    """
    choice = g.choice  # 获取选股列表
    position_size = g.position_size  # 每个股票的持仓大小
    lm_value = 0.8 * position_size  # 低于此值的持仓需要增加
    hm_value = 1.2 * position_size  # 高于此值的持仓需要减少
    cdata = get_current_data()  # 获取当前数据
    # 卖出操作
    for s in context.portfolio.positions:
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue  # 过滤停牌或价格异常的股票
        if s not in choice:
            log.info('sell', s, cdata[s].name)
            order_target(s, 0, MarketOrderStyle(0.99 * cdata[s].last_price))  # 卖出不在股票池中的股票
    # 买入操作
    for s in choice:
        if context.portfolio.available_cash < position_size:
            break  # 现金不足，停止买入
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue  # 过滤停牌或价格异常的股票
        if s not in context.portfolio.positions:
            log.info('buy', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01 * cdata[s].last_price))  # 买入不在持仓中的股票
        elif context.portfolio.positions[s].value < lm_value:
            log.info('balance+', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01 * cdata[s].last_price))  # 增加低于阈值的持仓
        elif context.portfolio.positions[s].value > hm_value:
            log.info('balance-', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(0.99 * cdata[s].last_price))  # 减少高于阈值的持仓
def iReport(context):
    """
    每日生成报告
    """
    g.days += 1  # 更新运行天数
    log.info('  positions', len(context.portfolio.positions))  # 打印当前持仓数量
    log.info('  return %.2f', 100 * context.portfolio.returns)  # 打印投资回报率
    log.info('  cash %.2f', context.portfolio.available_cash / 10000)  # 打印可用现金
    log.info('  value %.2f', context.portfolio.total_value / 10000)  # 打印投资组合总价值
    log.info('running days', g.days)  # 打印运行天数
```

### 策略说明

### 1. initialize(context)

**功能** : 初始化策略设置。此函数在策略启动时调用，主要用于配置策略的初始设置。

  * log.set_level('order', 'error')：设置日志级别为错误，避免记录过多信息。

  * set_option('use_real_price', True)：启用真实价格进行交易。

  * set_option('avoid_future_data', True)：避免使用未来数据。

  * g.days：初始化运行天数变量，用于记录策略的运行时间。

### 2. after_code_changed(context)

**功能** : 更新策略配置，当策略代码发生变化时调用。主要用于设置策略的调度任务。

  * unschedule_all()：取消所有已调度的任务。

  * run_daily(iUpdate, time='before_open')：每天开盘前调用 iUpdate 函数。

  * run_daily(iTrader, time='9:35')：每天9:35调用 iTrader 函数执行交易操作。

  * run_daily(iReport, time='after_close')：每天收盘后调用 iReport 函数生成报告。

### 3. iUpdate(context)

**功能** : 更新股票池和持仓信息。此函数在每个交易日开盘前调用，用于选择合适的股票进行投资。

  * nchoice：选择的股票数量。

  * nposition：最大持仓数量。

  * get_all_securities('stock', dt_last)：获取所有A股股票。

  * get_current_data()：获取当前市场数据。

  * stocks：过滤掉ST股票的股票列表。

  * get_fundamentals(query(...))：获取符合条件的股票信息，按照市场资本升序排序，并选择前 nchoice 只股票。

  * g.choice：更新选股列表。

  * g.position_size：计算每个股票的持仓大小，确保总持仓不超过总资产的1/nposition。

### 4. iTrader(context)

**功能** : 执行交易操作。此函数在每天9:35调用，用于根据更新后的股票池执行买入和卖出操作。

  * choice：选股列表。

  * position_size：每个股票的持仓大小。

  * lm_value：低于此值的持仓需要增加。

  * hm_value：高于此值的持仓需要减少。

  * cdata：当前市场数据。

  * **卖出操作** : 过滤停牌或价格异常的股票，卖出不在股票池中的股票。

  * **买入操作** : 过滤停牌或价格异常的股票，买入股票池中的股票。对于已持有的股票，根据持仓价值判断是否需要增加或减少持仓。

### 5. iReport(context)

**功能** : 生成每日投资报告。此函数在每天收盘后调用，用于记录和输出策略的运行状态。

  * g.days：更新运行天数。

  * log.info(...)：打印当前持仓数量、投资回报率、可用现金、投资组合总价值和运行天数。

### 总结

该策略通过动态因子筛选和市场条件判断进行股票交易。策略会定期更新选股池，依据持仓大小调整股票持仓，并每日生成投资报告。这种设计确保了策略的灵活性和及时响应市场变化。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
