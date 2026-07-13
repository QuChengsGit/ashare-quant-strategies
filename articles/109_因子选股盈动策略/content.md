# 109、因子选股盈动策略

这段策略代码实现了一个基于因子选股与动态调仓的量化投资策略，旨在通过数据驱动的模型来优化股票的选择与持仓调整。策略的核心包括利用情绪、质量、盈利能力等多重因子对股票进行筛选，并结合市场数据、基本面信息等进行分析，计算每只股票的总得分，从而确定投资组合。

每周，策略会根据最新的因子数据调整持仓，卖出不符合条件的股票并买入新的优质股票。此外，策略还通过每日检查涨停股的表现来进一步优化持仓，确保在波动市场中能够灵活调整，最大限度地降低风险并实现稳健回报。在回测和实时交易中，策略通过定时任务确保操作的及时性，采用严格的风险控制和交易成本设置，确保策略在实际市场中能够稳定运行。

**策略的完整代码下载地址请见文末最下方。**

### 1. **导入函数库**

```python
from jqdata import *  # 导入聚宽数据接口库
from jqfactor import *  # 导入聚宽因子库
import numpy as np  # 导入numpy库，用于数值计算
import pandas as pd  # 导入pandas库，用于数据处理
```

**详细说明** ：

  * jqdata：聚宽提供的金融数据接口库，主要用于获取历史数据（如股票价格、成交量等），因子数据（如财务因子），以及其他市场数据。

  * jqfactor：聚宽的因子库，包含了许多可用于量化策略的因子（如基本面因子、技术面因子等）。这些因子通常用于评估股票的投资价值。

  * numpy：数值计算库，用于数组运算、矩阵运算等处理。主要在量化策略中用于高效地处理数值数据。

  * pandas：数据分析库，用于数据框架处理，特别适合表格数据，广泛用于量化策略中的数据清洗、数据处理和表格计算。

### 2. **初始化函数**

```python
def initialize(context):
    # 设定基准指数为上证指数300
    set_benchmark('000905.XSHG')
    # 设置交易使用真实价格
    set_option('use_real_price', True)
    # 打开防止使用未来数据
    set_option("avoid_future_data", True)
    # 将滑点设置为0，即无滑点
    set_slippage(FixedSlippage(0))
    # 设置交易成本，包括开盘、平仓的手续费和印花税
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 只输出error级别的日志，避免大量无用信息
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10  # 最大持仓股票数
    g.hold_list = []  # 当前持仓股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票
    g.factor_list = [
        'ARBR',  # 情绪类因子 ARBR
        'SGAI',  # 质量类因子 销售管理费用指数
        'net_profit_to_total_operate_revenue_ttm',  # 质量类因子 净利润与营业总收入之比
        'retained_profit_per_share'  # 每股未分配利润
    ]
    # 设置交易策略运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 每天9:05执行准备股票池
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一9:30执行持仓调整
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 每天14:00检查涨停股票
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')  # 每天15:10打印持仓信息
```

**详细说明** ：

  * set_benchmark('000905.XSHG')：设置策略的基准为沪深300指数（代码：000905.XSHG），用于与策略收益进行比较，评估策略的表现。

  * set_option('use_real_price', True)：启用真实价格交易模式，意味着在实际交易时会以市场的最新价格成交，而非模拟价格。

  * set_option("avoid_future_data", True)：防止使用未来数据进行回测或实时交易，这是量化交易中的标准做法，避免"未来函数"的影响。

  * set_slippage(FixedSlippage(0))：设置滑点为零，确保在执行交易时，成交价格与预期价格一致。实际情况中，滑点通常会影响交易的效果。

  * set_order_cost(OrderCost(...))：设置交易成本，包括印花税（0.1%）、开盘和平仓的佣金（万分之三）等。这里设置了min_commission=5，表示最低手续费为5元。

  * log.set_level('order', 'error')：将日志级别设置为error，意味着只有在出现严重问题时，系统才会输出日志。这样可以减少无关的日志信息。

  * 全局变量 g 用于存储策略的运行状态，如最大持仓股票数量、持仓列表、昨日涨停股票列表以及因子列表。

**定时任务** ：

  * run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')：每天早上9:05运行 prepare_stock_list，用于更新股票池。

  * run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')：每周一的9:30运行 weekly_adjustment，进行持仓调整。

  * run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')：每天14:00运行 check_limit_up，检查昨日涨停的股票是否需要卖出。

  * run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')：每天15:10打印持仓信息，帮助实时监控当前的投资组合。

### 3. **准备股票池**

```python
def prepare_stock_list(context):
    # 获取当前持仓列表
    g.hold_list = []
    for position in list(context.portfolio.positions.values()):
        stock = position.security  # 获取持仓股票
        g.hold_list.append(stock)  # 添加到持仓列表
    # 获取昨日涨停的股票列表
    if g.hold_list != []:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]  # 选出涨停的股票
        g.yesterday_HL_list = list(df.code)  # 将涨停股票的代码添加到昨日涨停列表
    else:
        g.yesterday_HL_list = []  # 如果没有持仓，清空涨停股票列表
```

**详细说明** ：

  * g.hold_list 用于存储当前持仓的股票列表。通过访问 context.portfolio.positions 获取所有当前持有的股票。

  * get_price(g.hold_list, end_date=context.previous_date, frequency='daily', ...)：该函数调用获取 g.hold_list 中股票在昨日的每日价格数据。

  * df[df['close'] == df['high_limit']]：过滤出昨日收盘价等于涨停价的股票，这些股票是涨停股。

  * g.yesterday_HL_list 存储昨日涨停股票的代码列表，如果没有持仓，则清空该列表。

### 4. **选股模块**

```python
def get_stock_list(context):
    yesterday = context.previous_date  # 获取昨日的日期
    initial_list = get_all_securities().index.tolist()  # 获取所有股票代码
    initial_list = filter_new_stock(context, initial_list)  # 过滤新股
    initial_list = filter_kcbj_stock(initial_list)  # 过滤科创板股票
    initial_list = filter_st_stock(initial_list)  # 过滤ST股票
    # 获取因子值
    factor_values = get_factor_values(initial_list, [
        g.factor_list[0],
        g.factor_list[1],
        g.factor_list[2],
        g.factor_list[3],
    ], end_date=yesterday, count=1)  # 获取选定因子的值
    # 将因子值转换为DataFrame格式
    df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
    df[g.factor_list[0]] = list(factor_values[g.factor_list[0]].T.iloc[:, 0])
    df[g.factor_list[1]] = list(factor_values[g.factor_list[1]].T.iloc[:, 0])
    df[g.factor_list[2]] = list(factor_values[g.factor_list[2]].T.iloc[:, 0])
    df[g.factor_list[3]] = list(factor_values[g.factor_list[3]].T.iloc[:, 0])
    # 删除缺失数据
    df = df.dropna()
    # 根据因子权重计算总得分
    coef_list = [-2.3425, -694.7936, -170.0463, -1362.5762]
    df['total_score'] = coef_list[0]*df[g.factor_list[0]] + coef_list[1]*df[g.factor_list[1]] + coef_list[2]*df[g.factor_list[2]] + coef_list[3]*df[g.factor_list[3]]
    # 按总得分降序排序，得分越高未来表现越好
    df = df.sort_values(by=['total_score'], ascending=False)
    # 选择前10%的股票
    complex_factor_list = list(df.index)[:int(0.1*len(list(df.index)))]
    # 获取股票的市值和每股收益
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(complex_factor_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    # 过滤掉每股收益小于0的股票
    df = df[df['eps'] > 0]
    # 返回筛选后的股票列表
    final_list = list(df.code)
    return final_list
```

**详细说明** ：

  * 该函数通过因子选股的方式，利用多个财务和市场因子筛选出未来可能表现较好的股票。

  * get_all_securities() 获取所有可交易的股票列表。

  * filter_* 系列函数用于过滤不符合条件的股票，如新股、ST股、科创板股等。

  * get_factor_values 从聚宽因子库获取特定因子（如ARBR、SGAI等）的值，返回的数据会转换为 DataFrame 格式。

  * 使用不同因子的线性组合计算每只股票的 total_score，得分越高表示预测的未来收益越好。

  * 最后，选择得分最高的10%股票，并过滤掉每股收益小于0的股票，得到最终的股票池 final_list。

### 5. **整体调整持仓**

```python
def weekly_adjustment(context):
    # 获取应买入股票列表
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)  # 过滤停牌股票
    target_list = filter_limitup_stock(context, target_list)  # 过滤涨停股票
    target_list = filter_limitdown_stock(context, target_list)  # 过滤跌停股票
    # 截取最大持仓数量的股票
    target_list = target_list[:min(g.stock_num, len(target_list))]
    # 卖出不再持有的股票
    for stock in g.hold_list:
        if (stock not in target_list) and (stock not in g.yesterday_HL_list):
            log.info("卖出[%s]" % (stock))  # 卖出股票日志
            position = context.portfolio.positions[stock]
            close_position(position)  # 平仓
        else:
            log.info("已持有[%s]" % (stock))  # 股票仍持有
    # 买入新的股票
    position_count = len(context.portfolio.positions)
    target_num = len(target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)  # 根据现金分配买入股票
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):  # 开仓
                    if len(context.portfolio.positions) == target_num:
                        break
```

**详细说明** ：

  * get_stock_list(context) 获取更新后的选股池。

  * filter_paused_stock(target_list)、filter_limitup_stock 和 filter_limitdown_stock 分别用于过滤停牌、涨停和跌停的股票。

  * 策略根据最大持仓股票数 g.stock_num 截取选股池中的前 g.stock_num 只股票。

  * 对于不再在目标股票池中的股票，如果该股票不在昨日涨停股票列表中，则执行卖出操作（close_position(position)）。

  * 对于新增的股票，通过 open_position(stock, value) 进行买入操作，买入的资金由账户剩余现金和目标股票数决定。

**通过网盘分享的文件：代码.zip**

**下载链接:**[**https://pan.baidu.com/s/1rgJgkUGaL22IBnXEjN23vw**](<https://pan.baidu.com/s/1rgJgkUGaL22IBnXEjN23vw>)

**提取码: jgcf**

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
