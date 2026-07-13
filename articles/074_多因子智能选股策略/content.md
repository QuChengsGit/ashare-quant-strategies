# 74、多因子智能选股策略

# 策略概述

该策略综合使用多种因子（如波动性、成长性、反转性、杠杆、红利、价值、流动性、盈利性和质量）对股票进行评分，并根据得分高低选择优质股票进行投资。策略的核心是通过多因子模型对股票进行全方位评价，从而挑选出最具投资潜力的股票。策略使用沪深300指数（或上证指数）作为基准，并通过动态调整持仓来优化投资组合。

### 核心功能代码

```python
from jqdata import *
import numpy as np
import pandas as pd
from six import BytesIO
# 设置策略参数
def set_params():
    g.benchmark = '000001.XSHG'  # 上证指数
    g.stock_num = 10             # 持仓最大股票数
    g.sample_windows = 252        # 样本窗口长度
    g.buy_list = []
# 初始化函数
def initialize(context):
    set_params()
    set_benchmark(g.benchmark)                  # 设置基准
    set_option('use_real_price', True)          # 启用真实价格
    log.info('策略初始化')                       # 记录日志
    log.set_level('order', 'error')             # 设置日志级别
    # 设定定时任务
    run_weekly(before_market_open, weekday=1, time='before_open', reference_security='000300.XSHG')
    run_weekly(market_open, weekday=1, time='9:31', reference_security='000300.XSHG')
    run_weekly(after_market_close, weekday=1, time='after_close', reference_security='000300.XSHG')
# 设置交易费用
def set_trader(dt):
    set_slippage(FixedSlippage(0))  # 滑点设置为0
    if dt > datetime.datetime(2013, 1, 1):
        set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    elif dt > datetime.datetime(2011, 1, 1):
        set_order_cost(OrderCost(close_tax=0.001, open_commission=0.001, close_commission=0.001, min_commission=5), type='stock')
# 开盘前运行
def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    set_trader(context.current_dt)
    # 获取多因子评分并选择股票
    g.buy_list = get_comb_factor(context.current_dt).index.tolist()[:g.stock_num]
# 获取多因子组合评分
def get_comb_factor(current_dt):
    fac_dict = {
        '1_Volability': [('ivr_1m', True)],
        '2_Growth': [('yoy_eps_q', False), ('yoy_np_q', False), ('yoy_op_q', False), ('yoy_ocf_q', False)],
        '3_Reverse': [('mom_252d', True)],
        '4_Leverage': [('current_ratio', False), ('debt_asset_ratio', False), ('current_liab_ratio', True)],
        '5_Dividend': [('dividend_yield_ratio', True)],
        '6_Value': [('bp', False), ('cfp', False), ('sp', False), ('value_residual', True)],
        '7_Profit': [('roe', False), ('eps_adjust', False), ('grossmargin_ratio', False), ('grossprofit', False), ('roic', False)],
        '9_Quality': [('safexp_operrev', True), ('asset_turnover', False), ('fix_ratio', False)]
    }
    final_df = pd.DataFrame()
    for factor, metrics in fac_dict.items():
        data_file = f'data/{factor}/{str(current_dt.date())}.csv'
        data_df = pd.read_csv(BytesIO(read_file(data_file)), index_col=0)
        data_df[factor] = 0
        for metric, is_asc in metrics:
            top_stocks = data_df[metric].dropna().sort_values(ascending=is_asc).index[:len(data_df) // 10]
            data_df.loc[top_stocks, factor] += 1
        final_df[factor] = data_df[factor] / len(metrics)
    score_df = final_df.sum(axis=1).sort_values(ascending=False)
    return score_df
# 开盘时运行
def market_open(context):
    log.info('函数运行时间(market_open):' + str(context.current_dt.time()))
    hold_list = list(context.portfolio.positions.keys())
    log.info('持仓股票列表:' + str(hold_list))
    buy_list = g.buy_list
    log.info('买入股票列表:' + str(buy_list))
    # 卖出不在买入列表中的股票
    for stock in hold_list:
        if stock not in buy_list:
            order_target_value(stock, 0)
    # 平均分配资金购买新选出的股票
    capital_unit = context.portfolio.total_value / len(buy_list)
    log.info('单只股票分配资金:' + str(capital_unit))
    for stock in buy_list:
        order_target_value(stock, capital_unit)
# 收盘后运行
def after_market_close(context):
    log.info('函数运行时间(after_market_close):' + str(context.current_dt.time()))
    trades = get_trades()
    for trade in trades.values():
        log.info('成交记录：' + str(trade))
    log.info('一天结束')
# 过滤次新、科创、北交、ST、退市及停牌股票
def filter_stocks(all_security_df, yesterday, current_dt):
    all_security_df['index'] = all_security_df.index
    # 过滤次新股（上市时间少于375天）
    filter_fn = lambda t: (yesterday - t) >= datetime.timedelta(days=375)
    all_security_df = all_security_df[all_security_df['start_date'].apply(filter_fn)]
    # 过滤科创、北交所股票及特殊股票（ST、退市）
    filter_fn = lambda t: t[0] not in ['4', '8'] and t[:2] != '68'
    all_security_df = all_security_df[all_security_df['index'].apply(filter_fn)]
    st_df = get_extras('is_st', all_security_df.index, start_date=current_dt, end_date=current_dt, df=True).T
    st_list = st_df[st_df == True].dropna().index
    filter_fn = lambda t: ("ST" in t or "*" in t or "退" in t)
    all_security_df = all_security_df[(~all_security_df['index'].isin(st_list)) & (~all_security_df['display_name'].apply(filter_fn))]
    # 过滤停牌股票
    susp_df = get_price(all_security_df.index.tolist(), end_date=current_dt, count=1, frequency='daily', fields='paused', panel=False)
    unsusp_stocks = susp_df[susp_df['paused'] < 1]["code"].tolist()
    feasible_stocks = [s for s in unsusp_stocks if sum(attribute_history(s, 7, unit='1d', fields=('paused'), skip_paused=False)) == 0]
    return feasible_stocks
```

### 技术文档说明

1\. 策略参数设置 (set_params)

  * **功能** : 设置策略的全局参数，包括基准指数、持仓股票数量、样本窗口长度等。

  * **主要参数** :

    * g.benchmark: 基准指数，上证指数000001.XSHG。

    * g.stock_num: 持仓股票最大数量，默认10只。

2\. 初始化函数 (initialize)

  * **功能** : 初始化策略参数，设置基准、交易选项，并安排定时任务。

  * **任务** :

    * 每周一开盘前、开盘时、收盘后分别执行相关函数。

3\. 交易费用设置 (set_trader)

  * **功能** : 设置不同时间段的交易费率和滑点。

  * **逻辑** :

    * 根据不同的时间段，调整交易手续费。

4\. 开盘前运行函数 (before_market_open)

  * **功能** : 在开盘前获取多因子组合评分，筛选出符合条件的股票列表。

  * **逻辑** :

    * 调用get_comb_factor函数，得到根据多因子模型评分排序的股票列表。

5\. 多因子组合评分函数 (get_comb_factor)

  * **功能** : 综合使用多因子对股票进行评分，并根据得分高低进行排序。

  * **因子** :

    * 包含波动性、成长性、反转性、杠杆、红利、价值、盈利性和质量因子。

  * **逻辑** :

    * 对每个因子分别进行评分，然后综合得分并排序，筛选出前g.stock_num只股票。

6\. 开盘时运行函数 (market_open)

  * **功能** : 在开盘时执行买入和卖出操作，根据之前筛选出的股票列表调整持仓。

  * **逻辑** :

    * 卖

出不在买入列表中的股票。

  * 将可用资金均匀分配到选中的股票上。

7\. 收盘后运行函数 (after_market_close)

  * **功能** : 记录当天的交易日志，回顾成交情况。

8\. 股票过滤函数 (filter_stocks)

  * **功能** : 过滤不符合策略要求的股票，包括次新股、科创板、北交所、ST和退市股票，以及停牌股票。

  * **逻辑** :

    * 根据股票上市时间、市场板块、是否停牌等条件，筛选出可交易的股票列表。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
