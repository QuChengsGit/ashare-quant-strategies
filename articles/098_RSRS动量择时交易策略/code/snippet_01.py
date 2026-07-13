def initialize(context):
    set_benchmark('399006.XSHE')  # 设定基准指数
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 避免引入未来信息
    set_slippage(FixedSlippage(0.001))  # 设置固定滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='fund')
    log.set_level('order', 'error')  # 设置日志级别
    g.stock_pool = [
        '510050.XSHG', # 上证50ETF
        '159928.XSHE', # 中证消费ETF
        '510300.XSHG', # 沪深300ETF
        '159949.XSHE', # 创业板500ETF
    ]
    g.stock_num = 1  # 只买入评分最高的1只股票
    g.momentum_day = 20  # 动量计算的时间窗口
    g.ref_stock = '000300.XSHG'  # 用于择时的参考指数
    g.N = 18  # RSRS模型计算窗口
    g.M = 600  # RSRS标准分计算窗口
    g.score_threshold = 0.7  # RSRS择时信号阈值
    g.slope_series = initial_slope_series()[:-1]  # 初始化斜率序列
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(check_lose, time='open', reference_security='000300.XSHG')
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')
