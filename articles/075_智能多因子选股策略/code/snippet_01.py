from jqdata import *
from sklearn.svm import SVR
from jqlib.technical_analysis import *
import datetime
from jqfactor import *
import numpy as np
import pandas as pd
# 初始化函数
def initialize(context):
    set_benchmark('399303.XSHE')  # 设定基准
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 启用防未来函数
    set_slippage(FixedSlippage(0.02))  # 设置滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    log.set_level('order', 'error')  # 设置日志等级
    g.no_trading_today_signal = False
    g.stock_num = 5  # 持仓股票数量
    g.hold_list = []  # 当前持仓列表
    g.yesterday_HL_list = []  # 昨日涨停股票列表
    # 定时任务
    run_monthly(monthly_filter, 1, time='before_open')  # 每月第一天运行
    run_weekly(weekly_filter, -1, time='close')  # 每周最后一个交易日运行
    run_daily(prepare_stock_list, '9:05')  # 每日准备股票列表
    run_weekly(weekly_adjustment, 1, '9:30')  # 每周一调整持仓
    run_daily(check_limit_up, '14:00')  # 检查涨停股
    run_daily(close_account, '14:30')  # 收盘前调整持仓
    run_daily(print_position_info, '15:10')  # 打印持仓信息
    g.pools = set()  # 股票池
# 月度筛选函数
def monthly_filter(context):
    today = context.current_dt
    yestoday = today - datetime.timedelta(days=1)
    start_day = today - datetime.timedelta(days=375)
    # 小市值筛选
    q = query(valuation.code, valuation.circulating_market_cap).filter(
        valuation.circulating_market_cap.between(0, 30)).order_by(
        valuation.circulating_market_cap.asc()).limit(100)
    codes = get_fundamentals(q).code.tolist()
    # 过滤ST和次新股
    codes = filter_stocks(codes, start_day, yestoday)
    g.pools = set(codes)
# 每周筛选函数
def weekly_filter(context):
    yestoday = context.current_dt - datetime.timedelta(days=1)
    codes = filter_stocks(list(g.pools), None, yestoday)
    g.pools = set(codes)
# 准备股票列表
def prepare_stock_list(context):
    g.hold_list = list(context.portfolio.positions.keys())
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.yesterday_HL_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.yesterday_HL_list = []
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')
# 选股函数
def get_stock_list(context):
    final_list = set()
    initial_list = list(g.pools)
    yesterday = context.current_dt - datetime.timedelta(days=1)
    q = query(valuation.code, valuation.market_cap, valuation.turnover_ratio, valuation.pe_ratio,
              valuation.pb_ratio, valuation.ps_ratio, indicator.roa, income.total_operating_revenue).filter(
        valuation.code.in_(initial_list))
    dataset = get_fundamentals(q)
    dataset.columns = ['code', 'market_cap', '换手率', 'PE', 'PB', 'PS', '总资产收益率', '营业总收入']
    dataset = prepare_technical_factors(dataset, yesterday)
    X = dataset.drop('market_cap', axis=1)
    y = dataset['market_cap']
    svr = SVR()
    svr.fit(X, y)
    factor = y - pd.Series(svr.predict(X), index=y.index)
    final_list = list(factor.sort_values(ascending=True).index)[:g.stock_num]
    return final_list
# 计算技术指标因子
def prepare_technical_factors(dataset, date):
    dataset['平均差'] = DMA(dataset.code, date)[0].values()
    dataset['换手率'] = HSL(dataset.code, date)[0].values()
    dataset['移动平均'] = MA(dataset.code, date).values()
    dataset['乖离率'] = BIAS(dataset.code, date)[0].values()
    dataset['动量线'] = MTM(dataset.code, date).values()
    dataset.fillna(0, inplace=True)
    return dataset
# 调整持仓
def weekly_adjustment(context):
    if g.no_trading_today_signal:
        return
    target_list = get_stock_list(context)
    adjust_position(context, target_list)
# 调仓
def adjust_position(context, target_list):
    for stock in g.hold_list:
        if stock not in target_list and stock not in g.yesterday_HL_list:
            log.info("卖出[%s]" % stock)
            order_target(stock, 0)
        else:
            log.info("已持有[%s]" % stock)
    position_count = len(context.portfolio.positions)
    target_num = len(target_list)
    if target_num > position_count:
        value = context.portfolio.cash / (target_num - position_count)
        for stock in target_list:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == target_num:
                        break
# 检查涨停股
def check_limit_up(context):
    if not g.yesterday_HL_list:
        return
    for stock in g.yesterday_HL_list:
        current_data = get_price(stock, end_date=context.current_dt, frequency='1m', fields=['close', 'high_limit'],
                                 count=1, panel=False, fill_paused=True)
        if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
            log.info("[%s]涨停打开，卖出" % stock)
            order_target(stock, 0)
        else:
            log.info("[%s]涨停，继续持有" % stock)
# 过滤股票
def filter_stocks(codes, start_day, end_day):
    if start_day:
        codes = [code for code in codes if finance.STK_LIST.get_fundamentals(code).start_date <= start_day]
    st_df = get_extras('is_st', codes, end_date=end_day, count=1).T
    st_codes = st_df[st_df['is_st'] == 0].index.tolist()
    valid_codes = [code for code in st_codes if code[:2] in ('60', '00')]
    return valid_codes
# 判断是否为再平衡日期
def today_is_between(context, start_date, end_date):
    today = context.current_dt.strftime('%m-%d')
    return start_date <= today <= end_date
# 清仓后次日资金可转
def close_account(context):
    if g.no_trading_today_signal and g.hold_list:
        for stock in g.hold_list:
            order_target(stock, 0)
            log.info("卖出[%s]" % stock)
# 打印每日持仓信息
def print_position_info(context):
    trades = get_trades()
    for _trade in trades.values():
        print('成交记录：'+str(_trade))
    for position in context.portfolio.positions.values():
        print_position_details(position)
def print_position_details(position):
    print(f'代码:{position.security}')
    print(f'成本价:{position.avg_cost:.2f}')
    print(f'现价:{position.price}')
    print(f'收益率:{(100*(position.price/position.avg_cost-1)):.2f}%')
    print(f'持仓(股):{position.total_amount}')
    print(f'市值:{position.value:.2f}')
    print('———————————————————————————————————')
