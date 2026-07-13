from datetime import timedelta
from jqdata import *
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("match_by_signal", True)  # 强制撮合
    log.set_level('order', 'error')  # 过滤掉order系列API产生的比error级别低的log
    g.help_stock = {}  # 存储可能涨停的股票及其涨停价，格式：{股票代码：今日涨停价}
    g.max_stock_num = 20  # 最大持仓20只股票
    # 调度函数
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_run, time='every_bar', reference_security='000300.XSHG')
