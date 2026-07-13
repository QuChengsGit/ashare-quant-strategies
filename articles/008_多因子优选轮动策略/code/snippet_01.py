from jqdata import *
from jqfactor import get_factor_values
import numpy as np
import pandas as pd
import datetime

# 初始化函数
def initialize(context):
    # 设定基准指数
    set_benchmark('000905.XSHG')
    # 设置实盘交易
    set_option('use_real_price', True)
    # 防止未来数据泄露
    set_option("avoid_future_data", True)
    # 设置滑点为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    # 设置日志级别
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10  # 最大持股数
    g.limit_days = 20  # 最近买入并持有的时间窗口
    g.limit_up_list = []
    g.hold_list = []
    g.history_hold_list = []
    g.not_buy_again_list = []
    # 设置每日和每周的策略调度
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:40', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')

# 选股模块：通过因子筛选获取股票列表
def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame({'code': stock_list, 'score': score_list}).dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    return list(df['code'])[int(p1 * len(df)):int(p2 * len(df))]

# 获取最终选股列表
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    initial_list = filter_new_stock(context, initial_list, 250)

    # 筛选因子组合
    roa_list = get_factor_filter_list(context, initial_list, 'roa_ttm_8y', True, 0, 0.1)
    reps_list = get_factor_filter_list(context, initial_list, 'retained_earnings_per_share', True, 0, 0.1)
    nls_list = get_factor_filter_list(context, initial_list, 'non_linear_size', True, 0, 0.1)

    # 选股去重
    union_list = list(set(roa_list).union(set(reps_list)).union(set(nls_list)))
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(union_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    return list(df.code)

# 准备股票池并过滤
def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) > g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]

    g.not_buy_again_list = list(set(sum(g.history_hold_list, [])))
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']]['code'])
    else:
        g.high_limit_list = []

# 调整持仓
def weekly_adjustment(context):
    target_list = get_stock_list(context)
    target_list = filter_paused_stock(target_list)
    target_list = filter_limitup_stock(context, target_list)
    target_list = filter_limitdown_stock(context, target_list)
    recent_limit_up_list = get_recent_limit_up_stock(context, target_list, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in target_list if stock not in black_list][:g.stock_num]

    for stock in g.hold_list:
        if stock not in target_list and stock not in g.high_limit_list:
            close_position(context.portfolio.positions[stock])

    value = context.portfolio.cash / (g.stock_num - len(context.portfolio.positions))
    for stock in target_list:
        if context.portfolio.positions[stock].total_amount == 0:
            open_position(stock, value)

# 检查涨停股票并调整
def check_limit_up(context):
    if g.high_limit_list:
        for stock in g.high_limit_list:
            current_data = get_price(stock, end_date=context.current_dt, frequency='1m', fields=['close', 'high_limit'], panel=False)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                close_position(context.portfolio.positions[stock])

# 过滤停牌股票
def filter_paused_stock(stock_list):
    return [stock for stock in stock_list if not get_current_data()[stock].paused]

# 过滤ST股票
def filter_st_stock(stock_list):
    return [stock for stock in stock_list if not get_current_data()[stock].is_st]

# 获取涨停股票
def get_recent_limit_up_stock(context, stock_list, recent_days):
    stat_date = context.previous_date
    return [stock for stock in stock_list if len(get_price(stock, end_date=stat_date, frequency='daily', fields=['close', 'high_limit'], count=recent_days, panel=False)[get_price(stock, end_date=stat_date, frequency='daily', fields=['close', 'high_limit'], count=recent_days, panel=False)['close'] == get_price(stock, end_date=stat_date, frequency='daily', fields=['close', 'high_limit'], count=recent_days, panel=False)['high_limit']]) > 0]

# 过滤涨停股票
def filter_limitup_stock(context, stock_list):
    return [stock for stock in stock_list if get_current_data()[stock].last_price < get_current_data()[stock].high_limit]

# 过滤跌停股票
def filter_limitdown_stock(context, stock_list):
    return [stock for stock in stock_list if get_current_data()[stock].last_price > get_current_data()[stock].low_limit]

# 过滤次新股
def filter_new_stock(context, stock_list, days):
    return [stock for stock in stock_list if (context.previous_date - get_security_info(stock).start_date).days > days]

# 自定义交易模块
def order_target_value_(security, value):
    return order_target_value(security, value)

# 开仓
def open_position(security, value):
    return order_target_value_(security, value)

# 平仓
def close_position(position):
    return order_target_value_(position.security, 0)

# 打印持仓信息
def print_position_info(context):
    for position in context.portfolio.positions.values():
        print(f'代码:{position.security}, 成本价:{position.avg_cost:.2f}, 现价:{position.price}, 收益率:{(position.price/position.avg_cost - 1) * 100:.2f}%, 持仓(股):{position.total_amount}, 市值:{position.value:.2f}')
    print('————————————————————————分割线————————————————————————')
