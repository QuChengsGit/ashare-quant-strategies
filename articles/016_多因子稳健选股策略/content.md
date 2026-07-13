# 16、多因子稳健选股策略

### 策略概述

“多因子稳健选股策略”是一种基于多因子筛选的选股策略。该策略通过筛选低市净率、良好现金流、较高净资产收益率（ROA）和净利润增长率为正的股票，构建一个多元化的股票池，并定期调整持仓。每月初根据筛选条件调整持仓，同时避开创业板、科创板及北交所股票。

### 策略优化与详细代码说明

### 1. 初始化函数

**函数名：initialize**

```python
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 防止未来函数
    set_option("avoid_future_data", True)
    # 输出日志配置
    log.set_level('order', 'error')
    # 股票池及参数设置
    g.buy_stock_count = 5
    g.check_out_lists = []
    # 设置交易成本
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.00012, close_commission=0.00012, min_commission=5), type='stock')
    # 定时任务
    run_monthly(before_market_open, 1, time='5:00', reference_security='000300.XSHG')
    run_monthly(my_trade, 1, time='9:30', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
```

**说明** ：

  * 设置策略基准为沪深300，并开启动态复权和防止未来数据的功能。

  * 每月初调仓，并在每天收盘后打印持仓信息。

### 2. 开盘前选股函数

**函数名：before_market_open**

```python
def before_market_open(context):
    g.check_out_lists = []
    current_data = get_current_data()
    check_date = context.previous_date - datetime.timedelta(days=200)
    all_stocks = list(get_all_securities(date=check_date).index)
    # 过滤创业板、ST、停牌、涨停、跌停股票
    all_stocks = [stock for stock in all_stocks if not (
        (current_data[stock].day_open == current_data[stock].high_limit) or
        (current_data[stock].day_open == current_data[stock].low_limit) or
        current_data[stock].paused or
        current_data[stock].is_st or
        ('ST' in current_data[stock].name) or
        ('*' in current_data[stock].name) or
        ('退' in current_data[stock].name) or
        (stock.startswith(('30', '68', '8', '4')))
    )]
    # 多因子筛选
    q = query(
        valuation.code, valuation.market_cap, valuation.pe_ratio, income.total_operating_revenue
    ).filter(
        valuation.pb_ratio < 1,
        cash_flow.subtotal_operate_cash_inflow > 1e6,
        indicator.adjusted_profit > 1e6,
        indicator.roa > 0.15,
        indicator.inc_net_profit_year_on_year > 0,
        valuation.code.in_(all_stocks)
    ).order_by(
        indicator.roa.desc()
    ).limit(
        g.buy_stock_count * 3
    )
    check_out_lists = list(get_fundamentals(q).code)
    g.check_out_lists = check_out_lists[:g.buy_stock_count]
    log.info("今日股票池：%s" % g.check_out_lists)
```

**说明** ：

  * 在开盘前筛选股票，过滤不符合要求的股票并根据多因子条件筛选出最优股票。

  * 最终股票池从筛选出的股票中选出5只。

### 3. 交易执行模块

**函数名：my_trade**

```python
def my_trade(context):
    adjust_position(context, g.check_out_lists)
```

**说明** ：

  * 根据前述选股结果进行持仓调整。

**函数名：adjust_position**

```python
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        current_data = get_current_data()
        nosell_1 = context.portfolio.positions[stock].price >= current_data[stock].high_limit
        sell_2 = stock not in buy_stocks
        if sell_2 and not nosell_1:
            log.info("调出平仓：[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持仓，本次不买入：[%s]" % (stock))
    position_count = len(context.portfolio.positions)
    if g.buy_stock_count > position_count:
        value = context.portfolio.cash / (g.buy_stock_count - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.buy_stock_count:
                        break
```

**说明** ：

  * 按照筛选结果调整持仓，卖出不在新股票池中的股票，并买入新股票。

### 4. 辅助模块

**函数名：get_name**

```python
def get_name(stk):
    return get_security_info(stk).display_name + ':' + stk[:6]
```

**说明** ：

  * 获取股票的显示名称，用于日志记录。

**函数名：order_target_value_**

```python
def order_target_value_(security, value):
    if value == 0:
        log.debug("卖出 %s" % (get_name(security)))
    else:
        log.debug("买入 %s ，市值： %f" % (get_name(security), value))
    return order_target_value(security, value)
```

**说明** ：

  * 执行自定义买卖指令，记录交易日志。

**函数名：after_market_close**

```python
def after_market_close(context):
    positions_dict = context.portfolio.positions
    for position in list(positions_dict.values()):
        log.info("当前持仓:{0}, 数量:{1}, 市值:{2}, 盈利：{3}%, 建仓时间:{4}".format(
            get_name(position.security), position.total_amount, round(position.value, 0),
            round((position.value - (position.avg_cost * position.total_amount)) /
                  (position.avg_cost * position.total_amount) * 100, 1),
            position.init_time))
    log.info('#########################################################################################\n\n')
```

**说明** ：

  * 在每天收盘后记录持仓情况，包括持仓股票的数量、市值、盈利率等信息。

### 策略总结

“多因子稳健选股策略”通过筛选低市净率、高ROA、净利润增长的股票来构建多元化的投资组合，并定期调仓。该策略旨在提供稳定的收益，并避免过度的市场波动和风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
