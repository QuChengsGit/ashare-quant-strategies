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

复制
