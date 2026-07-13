# 64、多因子量化选股与动态调仓策略

### 策略介绍

**多因子量化选股与动态调仓策略** 是一种结合了基本面因子与技术面因子的多因子选股模型，通过机器学习模型进行分类预测，并在预测结果的基础上进行动态调仓和风险管理。该策略旨在从全市场股票中筛选出具备超额收益潜力的股票，并通过一系列止盈止损规则最大化收益并控制回撤。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
from jqdata import *
import numpy as np
import datetime
import pandas as pd
from jqfactor import get_factor_values, winsorize_med, standardlize, neutralize
from xgboost import XGBClassifier
import pickle
def initialize(context):
    # 设置基准
    g.benchmark = '399905.XSHE'  # 中证500
    set_benchmark(g.benchmark)
    # 设置选项
    set_option('avoid_future_data', True)
    set_option('use_real_price', True)
    log.set_level('order', 'error')  # 过滤掉低于error级别的日志
    # 策略参数
    g.all_A = True  # 是否全A选股
    g.signal = True  # 开仓信号
    g.alllist = []  # 股票池
    g.hold_list = []  # 今日持有的股票
    g.high_limit_list = []  # 前日涨停的股票
    g.stock_num = 10  # 最大持仓个数
    g.windows = 6  # 滚动训练窗口大小
    g.factor_cache = {}  # 因子缓存器
    g.regressor = XGBClassifier  # 选用模型
    g.params = {'max_depth': 3, 'learning_rate': 0.05, 'subsample': 0.8}  # 模型参数
    g.is_cv = False  # 是否交叉验证
    # 调度函数
    run_daily(before_market_open, time='9:05', reference_security='000300.XSHG')
    run_daily(market_open, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:30', reference_security='000300.XSHG')
```

技术说明：

  * **初始化** ：策略的初始化函数定义了基准指数、交易选项和日志级别，设置了选股模型的参数以及调度函数。

  * **多因子选股模型** ：使用XGBoost分类器，通过机器学习模型预测股票的涨跌概率，并筛选出得分最高的股票。

2\. 策略逻辑与选股模块

```python
def before_market_open(context):
    g.hold_list = list(context.portfolio.positions)
    if g.hold_list:
        yesterday = datetime.datetime.strftime(context.previous_date, '%Y-%m-%d')
        df = get_price(g.hold_list, end_date=yesterday, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.high_limit_list = []
    today = datetime.datetime.strftime(context.current_dt, '%Y-%m-%d')
    pre_m = datetime.datetime.strftime(context.previous_date, '%m')
    cur_m = datetime.datetime.strftime(context.current_dt, '%m')
    if cur_m != pre_m:
        g.signal = True
        stock_list = select_stocks(context)
        curr_stock_list = get_index_stocks('000002.XSHG', today) + get_index_stocks('399107.XSHE', today)
        curr_stock_list = list(set(curr_stock_list))
        g.alllist = [stk for stk in stock_list if stk in curr_stock_list]
    else:
        g.signal = False
        g.alllist = []
def select_stocks(context):
    # 构造训练集并训练模型
    date_list = get_period_date('M', start_date, yesterday)
    for date in date_list:
        if date not in g.factor_cache:
            factor_data = get_factor_data(stock_list, date)
            industry_code = list(get_industries('sw_l1', date).index)
            g.factor_cache[date] = data_preprocessing(factor_data, stock_list, industry_code, date)
    train_data = pd.concat([g.factor_cache[date] for date in date_list[:-1]], axis=0)
    train_target = train_data.pop('label')
    clf = g.regressor(**g.params)
    clf.fit(train_data.values, train_target.values)
    # 测试集选股
    test_data = g.factor_cache[date_list[-1]]
    prob = clf.predict_proba(test_data.values)[:, 1]
    df = pd.DataFrame(index=test_data.index)
    df['score'] = prob
    df = df.sort_values(by='score', ascending=False)
    stocks = df.head(int(0.1 * df.shape[0])).index.tolist()
    return stocks
```

技术说明：

  * **选股逻辑** ：基于过去的历史数据进行训练，生成多因子模型并对当前市场股票进行打分，选出得分最高的股票。

  * **因子处理** ：数据预处理包括去极值、中性化和标准化处理，确保因子数据的稳定性和可比性。

3\. 交易执行与动态调仓

```python
def market_open(context):
    if not g.signal:
        return
    buylist = filter_limit_stock(context, g.alllist)[:g.stock_num]
    for stock in context.portfolio.positions:
        if stock not in buylist and stock not in g.high_limit_list:
            order = order_target_value(stock, 0)
            if order is not None:
                log.info(f'卖出股票：{stock} 下单数量：{order.amount} 成交数量：{order.filled}')
    target_num = len(buylist)
    if target_num <= 0:
        return
    value = context.portfolio.total_value / target_num
    for stock in buylist:
        order = order_target_value(stock, value)
        if order is not None:
            log.info(f'调仓：{stock} 调整至金额：{value} 下单数量：{order.amount} 成交数量：{order.filled}')
def check_limit_up(context):
    now_time = context.current_dt
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close','high_limit'], count=1, panel=False)
            if current_data.iloc[0]['close'] < current_data.iloc[0]['high_limit']:
                order = order_target_value(stock, 0)
                if order is not None:
                    log.info(f'涨停打开-卖出股票：{stock} 下单数量：{order.amount} 成交数量：{order.filled}')
            else:
                log.info(f'{stock} 涨停，继续持有')
    g.high_limit_list = []
```

技术说明：

  * **动态调仓** ：根据选股结果，对未在选股名单中的持仓股票进行卖出操作，同时将资金重新分配到新的目标股票中。

  * **涨停板风险控制** ：对昨日涨停的股票进行特殊处理，确保涨停未打开时继续持有，一旦打开则立即卖出以防止回调风险。

### 策略优势

  * **多因子模型** ：结合基本面、技术面多因子模型，通过机器学习算法提升选股精度和收益的稳定性。

  * **动态调仓** ：通过定期更新股票池并动态调仓，保持投资组合的最佳状态。

  * **风险管理** ：采用多种止盈止损和涨停板处理策略，有效控制投资组合的风险。

### 总结

**多因子量化选股与动态调仓策略** 是一种基于多因子模型的量化选股策略，通过先进的机器学习算法进行股票预测和选股，并结合动态调仓和风险管理策略，能够在复杂市场环境中实现稳健的投资回报。该策略适合有一定数据处理能力和编程基础的量化投资者，尤其是在多因子模型构建和机器学习应用领域具有深入研究的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
