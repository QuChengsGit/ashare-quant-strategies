from jqdata import *
import datetime as dt
import pandas as pd
def initialize(context):
    # 系统设置
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)   
    log.set_level('system', 'error')
    # 最大持股数
    g.max_hold_num = 5
    g.prepare_stocks = []
    g.chosen_stocks = []  # 每天选出的待买股票
    g.holdable_days = 6  # 可持股天数
    g.hold_days = {}  # 持股天数
    g.need_sell = set()  # 待卖股
    # 调度函数
    run_daily(change_hold_info, time='8:30')
    run_daily(prepare_stocks, '9:05')
    run_daily(market_open, time='every_bar')
    run_daily(do_sell, time='14:40')
    run_daily(do_sell2, time='9:30')
