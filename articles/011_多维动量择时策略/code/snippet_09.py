def initialize(context):
    set_benchmark('399006.XSHE')  # 设定基准为创业板指数
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来数据
    set_slippage(FixedSlippage(0.001))  # 设置固定滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.000, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=0), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志级别
    # 股票池设置
    g.stock_pool = ['510300.XSHG', '510050.XSHG', '159949.XSHE', '159928.XSHE']
    g.stock_num = 1  # 持仓数量
    g.momentum_day = 20  # 动量参考天数
    g.ref_stock = '000300.XSHG'  # 基准指数
    g.N = 18  # 斜率计算参考天数
    g.M = 600  # RSRS标准分计算参考天数
    g.K = 8  # zscore斜率的窗口大小
    g.biasN = 90  # 乖离动量的时间天数
    g.lossN = 20  # 止损MA20的周期
    g.lossFactor = 1.005  # 止损比例
    g.SwitchFactor = 1.04  # 换仓位的比例
    g.Motion_1diff = 19  # 动量变化速度阈值
    g.raiser_thr = 4.8  # 股票前一天上涨比例阈值
    g.hold_stock = 'null'
    g.score_thr = -0.68  # RSRS标准分买入阈值
    g.score_fall_thr = -0.43  # RSRS标准分卖出阈值
    g.idex_slope_raise_thr = 12  # 大盘指数强势斜率阈值
    # 初始化斜率和RSRS标准分
    g.slope_series, g.rsrs_score_history = initial_slope_series()
    g.stock_motion = initial_stock_motion(g.stock_pool)  # 初始化动量因子
    # 定时运行函数
    run_daily(my_trade_prepare, time='7:00', reference_security='000300.XSHG')
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(my_sell2buy, time='9:35', reference_security='000300.XSHG')
    run_daily(check_lose, time='open', reference_security='000300.XSHG')
    run_daily(pre_hold_check, time='11:25')
    run_daily(hold_check, time='11:27')

复制
