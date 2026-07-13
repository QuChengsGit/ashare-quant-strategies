import pandas as pd
from jqdata import *
def initialize(context):
    log.set_level('order', 'error')  # 设置日志输出级别为error
    set_option('use_real_price', True)  # 启用动态复权模式
    set_option('avoid_future_data', True)  # 避免未来数据
    g.days = 0  # 初始化天数计数器
def after_code_changed(context):
    unschedule_all()  # 取消所有之前设定的定时任务
    run_daily(iUpdate, time='before_open')  # 开盘前更新选股池
    run_daily(iTrader, time='9:35')  # 市场开盘后的交易策略
    run_daily(iReport, time='after_close')  # 收盘后报告投资组合情况

复制
