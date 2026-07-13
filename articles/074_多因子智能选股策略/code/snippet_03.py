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
