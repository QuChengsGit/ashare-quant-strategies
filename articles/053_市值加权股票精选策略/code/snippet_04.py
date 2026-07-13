from jqdata import *
def initialize(context):
    set_benchmark('399303.XSHE')  # 设置基准指数为创业板综指
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 避免使用未来数据进行回测
    log.set_level('system', 'error')  # 设置日志级别为错误，减少冗余输出
    g.stock_num = 400  # 设置选股数量
    run_daily(rebalance, '9:30')  # 每日9:30进行调仓

复制
