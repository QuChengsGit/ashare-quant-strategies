from jqdata import *
from jqfactor import *
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
def initialize(context):
    set_benchmark('000985.XSHG')  # 设定中证全指为基准
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    log.set_level('order', 'error')
    g.no_trading_today_signal = False
    g.stock_num = 3  # 持股数量上限
    g.hold_list = []  # 当前持仓列表
    g.yesterday_HL_list = []  # 昨日涨停股列表
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00')
    run_daily(close_account, '14:50')

复制
