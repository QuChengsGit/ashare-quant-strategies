from jqdata import *
import numpy as np
from sklearn.svm import SVR
import pandas as pd
def initialize(context):
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')
    set_benchmark('000300.XSHG')  # 设置沪深300为基准
    g.stock_num = 10  # 目标持仓股票数量
    g.curstaut = 0  # 0 表示当前空仓，1 表示满仓
    g.ref_stock = '000001.XSHG'  # 选取上证指数作为参考指数
    g.N = 18  # 计算斜率和拟合度参考的天数
    g.M = 600  # 计算标准分zscore参考的天数
    g.K = 8  # 计算 zscore 斜率的窗口大小
    g.score_thr = -1  # RSRS标准分的买入阈值
    g.score_fall_thr = -0.5  # RSRS标准分的卖出阈值
    g.idex_slope_raise_thr = 10  # 指数斜率上升判断标准
    g.slope_series, g.rsrs_score_history = initial_slope_series()  # 初始化斜率和RSRS评分历史
    run_daily(my_trade_prepare, time='9:00', reference_security='000300.XSHG')
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')

复制
