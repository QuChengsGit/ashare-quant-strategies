# 108、多维稳健 Alpha 策略

“多维稳健 Alpha 策略”是一种结合了**基本面分析** 、**行业轮动** 和**市场行为约束** 的量化投资策略。该策略的核心目标是在控制下行风险的同时，稳定地获取超额收益（Alpha）。其通过多维度因子的筛选与组合，采用严格的风险控制和动态的调仓机制，力求在不同的市场环境下实现持续的稳健增长。**策略的完整代码和回测数据请见本文最下方。**

策略的基本原则是：**通过深入的基本面分析选出具备长期增长潜力的股票，并通过行业与市场的过滤机制避免高波动、低景气的股票** 。这一方法不仅确保了投资组合的稳健性，还能最大化地挖掘市场中潜在的超额回报。

### 选股逻辑

在选股方面，“多维稳健 Alpha 策略”注重对标的股票进行严格的筛选。首先，在**基本面筛选** 上，策略通过财务指标，如市盈率（PE）、市净率（PB）以及净资产收益率（ROE），选取具备较高盈利能力、合理估值的优质个股。其次，**行业过滤** 是该策略的另一大亮点。通过对不具备成长潜力或景气度较差的行业进行剔除，如周期性行业、政策风险较高的行业，策略确保了投资组合的高质量和高成长性。最后，**市场行为约束** 方面，策略剔除流动性差、波动性大的个股，如涨停或跌停股票，以此降低市场波动带来的不必要风险。

### 策略优势

“多维稳健 Alpha 策略”在多个方面展现了其独特的优势。首先，**稳健性** 是策略的最大特点，通过多维因子筛选与严格的风险控制，使得投资组合的波动性大大降低，适合长期持有。其次，**超额收益** 的来源清晰明确，Alpha 主要来自于估值修复和盈利增长的驱动，而不是单纯的市场波动或市场整体的增长。因此，策略的收益更加稳定且可持续。此外，策略具备很强的**可扩展性** ，随着市场环境的变化，新的因子可以被纳入模型，以进一步优化策略的表现。最后，**动态调仓** 和**事件驱动机制** 让该策略能够灵活应对市场波动，在短期市场冲击中减少不必要的损失。

### 适用场景

“多维稳健 Alpha 策略”特别适合**中低风险偏好** 的投资者，尤其适用于那些希望在波动较大的市场中实现稳健回报的机构投资者。对于注重风险控制、同时又希望在长期内获得稳定增长的投资者，这一策略无疑是一种理想的选择。通过精细的因子筛选和动态的风险管理，策略能够在震荡市中持续捕捉有价值的投资机会，确保回报的稳定性和可持续性。



### 1. **导入函数库**

```python
from jqdata import *
from jqlib.technical_analysis import *
from jqfactor import get_factor_values
import numpy as np
import pandas as pd
import statsmodels.api as sm
import datetime as dt
```

**库的功能** ：

  * **jqdata** : 聚宽（JoinQuant）提供的基础数据接口库，允许我们访问股票市场数据（如历史行情数据、股票基本面、公司财报等），这些数据通常用于量化分析和回测。

  * **jqlib.technical_analysis** : 聚宽的技术分析库，提供常见的技术指标计算（如MACD、KDJ、RSI等），这些指标通常用于短期市场预测。

  * **jqfactor.get_factor_values** : 聚宽因子库，专注于金融因子的计算，如价值因子（PE、PB）、成长因子（ROE）、波动性因子等，帮助筛选优质股票。

  * **numpy** : 数值计算库，支持高效的矩阵操作和数学计算，适用于量化交易中对股票数据的计算和分析。

  * **pandas** : 数据处理库，提供强大的数据结构和操作方法，特别适合量化交易中对时间序列和数据框的处理。

  * **statsmodels.api** : 统计模型库，提供回归分析、时间序列分析等功能，常用于构建和评估统计模型。

  * **datetime** : 时间日期处理模块，常用于数据时间的计算和转换，如日期差异计算。



### 2. **初始化函数 (initialize)**

```python
def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准指数为中证500指数
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志级别为错误，过滤低级别日志
    # 初始化全局变量
    g.stock_num = 10  # 设置最大持仓数为10
    g.limit_up_list = []  # 用于记录涨停的股票
    g.hold_list = []  # 当前持仓股票
    g.history_hold_list = []  # 记录过去持仓的股票
    g.not_buy_again_list = []  # 不再买入的股票列表
    g.limit_days = 20  # 设置不再买入股票的时间段为20天
    g.target_list = []  # 预操作股票池
    g.industry_control = True  # 是否过滤不看好的行业
    g.industry_filter_list = ['钢铁I','煤炭I','石油石化I','采掘I', '银行I','非银金融I','金融服务I', '交运设备I','交通运输I','传媒I','环保I']  # 不看好的行业列表
```

**初始化设置功能** ：

  * **set_benchmark('000905.XSHG')** : 设置一个基准指数（中证500指数）。量化策略通常会将投资组合的表现与基准指数进行比较，评估策略的效果。

  * **set_option('use_real_price', True)** : 启用真实价格交易模式，这意味着在回测过程中，策略将按照市场实际成交价格进行买卖，而不是模拟价格。

  * **set_option("avoid_future_data", True)** : 避免策略在回测过程中使用未来的数据，确保回测结果的真实性，防止“未来数据污染”策略表现。

  * **set_slippage(FixedSlippage(0))** : 设置滑点为0，滑点是指买卖时的价格差异，0表示不存在价格偏差。在实际交易中，滑点通常会影响策略的执行，设置为0是为了简化回测。

  * **set_order_cost** : 设置交易的费用结构，包括：

    * open_tax=0: 买入时不收取税费。

    * close_tax=0.001: 卖出时收取千分之一的税费。

    * open_commission=0.0003: 买入时收取千分之三的手续费。

    * close_commission=0.0003: 卖出时收取千分之三的手续费。

    * min_commission=5: 设置最低交易手续费为5元。

  * **log.set_level('order', 'error')** : 设置日志级别为“error”，确保只记录关键信息，避免过多无用信息。

  * **全局变量初始化** :

    * g.stock_num = 10: 最大持仓数目，控制最多持有10只股票。

    * g.limit_up_list, g.hold_list, g.history_hold_list, g.not_buy_again_list: 用于记录不同的股票列表，包括涨停股、当前持股、历史持股、禁买股等。

    * g.limit_days = 20: 设置持股禁买的天数，如果某只股票在过去20天内已经买过并涨停，将不会再次买入。

    * g.target_list: 预操作的股票池，即候选的股票。



### 3. **选股模块 (get_stock_list)**

```python
def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = get_all_securities().index.tolist()  # 获取所有股票
    initial_list = filter_new_stock(context, initial_list)  # 过滤掉新股
    initial_list = filter_kcb_stock(context, initial_list)  # 过滤科创板股票
    initial_list = filter_st_stock(initial_list)  # 过滤掉ST股
    # PB过滤
    q = query(valuation.code, valuation.pb_ratio, indicator.eps).filter(valuation.code.in_(initial_list)).order_by(valuation.pb_ratio.asc())
    df = get_fundamentals(q)  # 获取PB和EPS数据
    df = df[df['eps'] > 0]  # 只保留盈利大于0的股票
    df = df[df['pb_ratio'] > 0]  # 只保留PB大于0的股票
    pb_list = list(df.code)[:int(0.5 * len(df.code))]  # 选取PB最小的一半股票
    # ROE过滤
    interval = 1000
    pb_len = len(pb_list)
    if pb_len <= interval:
        df = get_history_fundamentals(pb_list, fields=[indicator.code, indicator.roe], watch_date=yesterday, count=5, interval='1q')
    else:
        df_num = pb_len // interval
        df = get_history_fundamentals(pb_list[:interval], fields=[indicator.code, indicator.roe], watch_date=yesterday, count=5, interval='1q')
        for i in range(df_num):
            dfi = get_history_fundamentals(pb_list[interval*(i+1):min(pb_len,interval*(i+2))], fields=[indicator.code, indicator.roe], watch_date=yesterday, count=5, interval='1q')
            df = df.append(dfi)
    df = df.groupby('code').apply(lambda x: x.reset_index()).roe.unstack()  # 获取ROE数据
    df['increase'] = 4 * df.iloc[:, 4] - df.iloc[:, 0] - df.iloc[:, 1] - df.iloc[:, 2] - df.iloc[:, 3]  # 计算ROE的增长量
    df.dropna(inplace=True)  # 删除缺失值
    df.sort_values(by='increase', ascending=False, inplace=True)  # 按照ROE增长排序
    temp_list = list(df.index)
    temp_len = len(temp_list)
    roe_list = temp_list[:int(0.1 * temp_len)]  # 选取ROE增长前10%的股票
    # 行业过滤
    if g.industry_control:
        industry_df = get_stock_industry(roe_list, yesterday)
        ROE_list = filter_industry(industry_df, g.industry_filter_list)
    else:
        ROE_list = roe_list
    # 市值排序
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(ROE_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)  # 获取市值数据
    ROEC_list = list(df.code)
    return ROEC_list
```

**选股功能** ：

  * **get_all_securities()** : 获取所有可交易的证券（股票、基金等）。

  * **filter_new_stock** : 过滤掉新上市的股票，以避免选择还未稳定的股票。

  * **filter_kcb_stock** : 过滤掉科创板股票（在一些策略中，科创板股票因其高波动性可能不适合）。

  * **filter_st_stock** : 过滤掉ST股（退市风险股票）。

  * **PB过滤** ：

    * 使用**市净率PB** （Price-to-Book）来筛选股票，低PB一般意味着股票被低估，可能是价值型投资的选择。

    * 筛选出**盈利大于0** 的股票，剔除亏损公司。

  * **ROE过滤** ：

    * 使用**ROE** （Return on Equity）来评估股票的盈利能力，选择ROE增长率较高的股票。

    * df['increase'] = 4 * df.iloc[:, 4] - df.iloc[:, 0] - df.iloc[:, 1] - df.iloc[:, 2] - df.iloc[:, 3] 这一行计算ROE的增长量，通过对过去四个季度的ROE数据进行加权和计算。

  * **行业过滤** ：

    * 根据指定的行业筛选股票，避免选择一些不看好的行业（如钢铁、煤炭等）。

  * **市值排序** ：

    * 最后对筛选出的股票按**市值** 进行排序，选择市值适中的股票进行投资。



### 4. **准备股票池 (prepare_stock_list)**

```python
def prepare_stock_list(context):
    g.hold_list = []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        for stock in hold_list:
            temp_set.add(stock)
    g.not_buy_again_list = list(temp_set)
    if g.hold_list != []:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        df = df[df['close'] == df['high_limit']]
        g.high_limit_list = list(df.code)
    else:
        g.high_limit_list = []
```

**功能解释** ：

  * **持仓管理** ：遍历当前的投资组合，获取所有当前持有的股票（g.hold_list）。

  * **历史持仓** ：记录过去一段时间的持仓，避免短期内频繁交易同一只股票。

  * **禁买股列表** ：通过计算过去一段时间内的持仓股票，创建一个not_buy_again_list，确保在某段时间内不会重复买入同一只股票。

  * **涨停股检查** ：在g.hold_list中，检查哪些股票已经涨停（即当前价格等于涨停价格），并将这些股票加入到g.high_limit_list中，后续可以根据涨停情况决定是否继续持有。



5\. **每周调整持仓 (weekly_adjustment)**

```python
def weekly_adjustment(context):
    g.target_list = get_stock_list(context)[:10]  # 获取前10只符合条件的股票
    g.target_list = filter_paused_stock(g.target_list)  # 过滤停牌股票
    g.target_list = filter_limitup_stock(context, g.target_list)  # 过滤涨停股票
    g.target_list = filter_limitdown_stock(context, g.target_list)  # 过滤跌停股票
    recent_limit_up_list = get_recent_limit_up_stock(context, g.target_list, g.limit_days)  # 获取最近有涨停的股票
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))  # 排除黑名单中的股票
    g.target_list = [stock for stock in g.target_list if stock not in black_list]  # 过滤掉黑名单中的股票
    g.target_list = g.target_list[:min(g.stock_num, len(g.target_list))]  # 限制最多持仓的股票数
    # 卖出不符合条件的股票
    for stock in g.hold_list:
        if stock not in g.target_list and stock not in g.high_limit_list:
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
    # 买入符合条件的股票
    position_count = len(context.portfolio.positions)
    target_num = len(g.target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)
        for stock in g.target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == target_num:
                        break
```

**功能解释** ：

  * **选取股票池** ：每周调整一次持仓，首先从选股模块获取一个新的股票池（g.target_list），筛选出符合条件的前10只股票。

  * **过滤股票** ：在筛选出的股票中，过滤掉停牌股、涨停股、跌停股等不符合条件的股票。

  * **避免重复买入** ：根据过去的持股记录（not_buy_again_list），避免买入近期已经买过并涨停的股票。

  * **调整持仓** ：

    * 如果当前持仓数目不足，使用现有资金买入新股票，确保持仓数量不会超过最大持仓数（g.stock_num）。

    * 卖出不符合条件的股票（不在目标池中的股票）。



### 6. **检查涨停股票 (check_limit_up)**

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list != []:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close','high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0,0] < current_data.iloc[0,1]:
                log.info("[%s]涨停打开，卖出" % (stock))
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info("[%s]涨停，继续持有" % (stock))
```

**功能解释** ：

  * **检查涨停股票** ：遍历持仓中的涨停股票，若涨停打开（即当前价格小于涨停价），则卖出该股票；如果股票继续涨停，则继续持有。



## 总结：

这段代码实现了一个基于量化的自动选股和调仓策略，包含了多个功能模块：

  * 初始化设置和日志管理；

  * 股票筛选（包括财务筛选和技术指标筛选）；

  * 股票池的动态管理（包括持仓和目标池）；

  * 每周调仓和调整持仓；

  * 处理涨停股票并进行操作；

  * 交易成本的设定。

通过这些功能，该策略能够根据预设的财务和市场指标动态调整投资组合，自动买卖股票，从而实现量化投资目标。

**代码下载地址：**

**链接:** <https://pan.baidu.com/s/1ELmDdzCNjq7ECFfHwdGHfg>

**提取码: ewin**

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
