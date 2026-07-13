from jqdata import *
import warnings
def initialize(context):
    set_slippage(FixedSlippage(0.02))  # 设置固定滑点
    set_benchmark('000300.XSHG')  # 设置基准指数为沪深300
    set_option('use_real_price', True)  # 开启动态复权模式
    set_option('avoid_future_data', True)  # 避免未来数据
    log.set_level('order', 'error')  # 设置日志输出级别为error
    warnings.filterwarnings('ignore')  # 过滤警告信息
    # 全局变量设置
    g.stock_num = 5  # 最大股票持仓数量
    g.position = 1  # 仓位比例
    # 设置交易时间，每月第一个交易日执行交易函数
    run_monthly(my_trade, monthday=1, time='10:00', reference_security='000300.XSHG')
