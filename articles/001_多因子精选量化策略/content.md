# 1、多因子精选量化策略

# 1. 策略概述

该量化交易策略基于多因子模型，通过因子评分选股，并进行每周调仓。策略包含了基础的风险管理措施，如过滤停牌、ST、涨跌停股票等。优化后的策略改进了选股和调仓逻辑，增加了投资组合的灵活性和鲁棒性。



## 2. 代码结构概览

  * **初始化函数** (initialize): 设置策略的基础配置，包括基准、交易参数、初始化全局变量、以及定时任务。

  * **准备股票池** (prepare_stock_list): 每日生成当前持仓股票列表和昨日涨停股票列表。

  * **选股模块** (get_stock_list): 根据因子计算和排序，筛选出符合条件的股票。

  * **整体调整持仓** (weekly_adjustment): 每周根据选股结果调整持仓，卖出不符合条件的股票，买入新股票。

  * **检查涨停股票** (check_limit_up): 检查昨日涨停股票是否继续涨停，否则卖出。

  * **过滤模块** ：提供多种过滤函数，用于过滤停牌、ST、涨跌停、科创板、次新股等。

  * **交易模块** ：包括自定义下单、开仓、平仓等功能。

  * **日志与调试** ：打印持仓信息及交易记录，方便调试和跟踪策略运行情况。



# 3. 详细代码解释

## 3.1 初始化函数 (initialize)

```python
def initialize(context):
    # 设定基准指数为中证500指数
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 启用防未来函数，避免未来数据干扰策略
    set_option("avoid_future_data", True)
    # 设置滑点为0，模拟理想交易环境
    set_slippage(FixedSlippage(0))
    # 设置交易成本，考虑买卖佣金和税率
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 过滤低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.no_trading_today_signal = False
    g.stock_num = 1  # 默认持有股票数量为1
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 昨日涨停的股票列表
    # 多因子模型因子及权重
    g.factor_list = [
        (['ARBR', 'SGAI', 'net_profit_to_total_operate_revenue_ttm', 'retained_profit_per_share'],
         [-2.3425, -694.7936, -170.0463, -1362.5762]),
        (['Price1Y', 'total_profit_to_cost_ratio', 'VOL120'],
         [-0.0647128120839873, -0.006385116279168804, -0.0029867925845833217]),
        (['price_no_fq', 'total_profit_to_cost_ratio', 'inventory_turnover_rate'],
         [-6.123355346008858e-05, -0.002579342458393642, -2.194257357346814e-06]),
        (['debt_to_assets', 'operating_cost_to_operating_revenue_ratio', 'DAVOL20', 'price_no_fq', 'sales_growth'],
         [0.04477354820057883, 0.021636407482421707, -0.01864268317469762, -0.0004678118383947827, 0.02884867440332058]),
        (['TVSTD6', 'cashflow_per_share_ttm', 'sharpe_ratio_120', 'non_operating_net_profit_ttm'],
         [-5.394060941494863e-12, 4.6306072704138405e-05, -0.0030567075906980912, 1.4227113275455325e-12])
    ]
    # 设置定时任务
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00')
    run_daily(close_account, '14:30')
    run_daily(print_position_info, '15:10')
```

**功能** ：初始化策略的基本配置，设定交易成本、滑点及多因子模型。全局变量用于存储持仓、因子和调仓信息。



## 3.2 准备股票池 (prepare_stock_list)

```python
def prepare_stock_list(context):
    # 获取当前持仓股票列表
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    # 获取昨日涨停的股票
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.yesterday_HL_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.yesterday_HL_list = []
    # 判断今天是否为资金再平衡日
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')
```

**功能** ：每天开盘前生成当前持仓股票列表，判断是否为资金再平衡日，并更新昨日涨停股票列表。



## 3.3 选股模块 (get_stock_list)

```python
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities('stock', yesterday).index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    final_list = []
    for factor_list, coef_list in g.factor_list:
        factor_values = get_factor_values(initial_list, factor_list, end_date=yesterday, count=1)
        df = pd.DataFrame({factor: factor_values[factor].iloc[0] for factor in factor_list}, index=initial_list)
        df = df.dropna()
        # 计算因子得分
        df['total_score'] = sum(coef_list[i] * df[factor_list[i]] for i in range(len(factor_list)))
        df = df.sort_values(by='total_score', ascending=False)
        # 进一步筛选基本面良好的股票
        selected_stocks = list(df.index)[:int(0.1 * len(df))]
        q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(selected_stocks)).order_by(valuation.circulating_market_cap.asc())
        df = get_fundamentals(q)
        df = df[df['eps'] > 0]
        filtered_stocks = filter_paused_stock(list(df.code))
        filtered_stocks = filter_limitup_stock(context, filtered_stocks)
        filtered_stocks = filter_limitdown_stock(context, filtered_stocks)
        final_list.extend(filtered_stocks[:g.stock_num])
    return final_list
```

**功能** ：基于多因子模型筛选股票，计算得分并排序，最后返回符合条件的股票列表。



## 3.4 持仓调整 (weekly_adjustment)

```python
def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        # 卖出不符合条件的股票
        for stock in g.hold_list:
            if stock not in target_list and stock not in g.yesterday_HL_list:
                close_position(context.portfolio.positions[stock])
                log.info(f"卖出[{stock}]")
        # 买入新股票
        position_count = len(context.portfolio.positions)
        if len(target_list) > position_count:
            value_per_stock = context.portfolio.cash / (len(target_list) - position_count)
            for stock in target_list:
                if context.portfolio.positions[stock].total_amount == 0:
                    open_position(stock, value_per_stock)
                    if len(context.portfolio.positions) == len(target_list):
                        break
```

**功能** ：每周一调整持仓，卖出不再符合条件的股票，并买入符合条件的新股票，保持仓位平衡。



## 3.5 调整昨日涨停股票 (check_limit_up)

```python
def check_limit_up(context):
    now_time = context.current_dt
    for stock in g.yesterday_HL_list:
        data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], count=1, panel=False)
        if data.iloc[0, 0] < data.iloc[0, 1]:
            close_position(context.portfolio.positions[stock])
            log.info(f"[{stock}]涨
停打开，卖出")
        else:
            log.info(f"[{stock}]涨停，继续持有")
```

**功能** ：检查昨日涨停股票，如果涨停打开则卖出，否则继续持有。



## 3.6 过滤模块

```python
def filter_paused_stock(stock_list):
    return [stock for stock in stock_list if not get_current_data()[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if stock[0] not in ['4', '8'] and not stock.startswith('68')]
def filter_limitup_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions or current_data[stock].close < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions or current_data[stock].close > current_data[stock].low_limit]
def filter_new_stock(context, stock_list):
    return [stock for stock in stock_list if context.previous_date - get_security_info(stock).start_date >= datetime.timedelta(days=375)]
```

**功能** ：提供多种过滤函数，排除停牌、ST、涨跌停、科创板和次新股，确保选股稳定性。



## 3.7 交易模块

```python
def order_target_value_(security, value):
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order and order.filled > 0
def close_position(position):
    return order_target_value_(position.security, 0)
```

**功能** ：实现自定义下单、开仓、平仓功能。



## 3.8 账户管理 (close_account, print_position_info)

```python
def close_account(context):
    if g.no_trading_today_signal and g.hold_list:
        for stock in g.hold_list:
            close_position(context.portfolio.positions[stock])
            log.info(f"卖出[{stock}]")
def print_position_info(context):
    for position in context.portfolio.positions.values():
        log.info(f"代码: {position.security}，持仓(股): {position.total_amount}，市值: {position.value}，收益率: {100 * (position.price / position.avg_cost - 1):.2f}%")
```

**功能** ：处理清仓和输出持仓信息，帮助用户跟踪账户状况。



# 4. 策略总结

该策略使用多因子模型进行股票筛选，通过严格的过滤条件确保选股质量，并每周调整持仓。策略内置了多种风险管理机制，包括检查涨停、过滤不合格股票等。通过灵活的持仓调整机制，策略能够在不同市场条件下保持稳健运行。

**如果您想将文中的策略转换为适配QMT/Ptrade的代码，可以使用下面的转换工具：**

https://vxqn28ptbw.coze.site/

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
