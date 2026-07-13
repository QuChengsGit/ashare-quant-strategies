def initialize(context):
    set_benchmark('399006.XSHE')  # 设定创业板指作为基准
    set_option('use_real_price', True)  # 使用实时价格进行交易
    set_option("avoid_future_data", True)  # 避免未来函数
    set_slippage(FixedSlippage(0.001))  # 固定滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.000, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=0), type='fund')
    log.set_level('order', 'error')  # 设定日志等级
    g.stock_pool = [
        '510300.XSHG',  # 沪深300ETF
        '510050.XSHG',  # 上证50ETF
        '159949.XSHE',  # 创业板50
    ]
    g.stock_num = 1  # 买入评分最高的前1只ETF
    g.momentum_day = 20  # 动量因子计算窗口
    g.ref_stock = '000300.XSHG'  # 用沪深300指数作为择时计算的基础
    g.N = 18  # 计算斜率和拟合度的窗口
    g.M = 600  # 标准分的计算周期
    g.K = 8  # zscore 斜率的窗口大小
    g.biasN = 90  # 乖离动量的时间窗口
    g.lossN = 20  # 止损的周期
    g.lossFactor = 1.005  # 下跌止损的比例
    g.SwitchFactor = 1.04  # 换仓比例阈值
    g.Motion_1diff = 19  # 动量变化阈值
    g.raiser_thr = 4.8  # 股票前一天上涨比例阈值
    g.hold_stock = 'null'
    g.score_thr = -0.68  # RSRS分数买入阈值
    g.score_fall_thr = -0.43  # RSRS分数卖出阈值
    g.idex_slope_raise_thr = 12  # 指数斜率买入阈值
    g.slope_series, g.rsrs_score_history = initial_slope_series()
    g.stock_motion = initial_stock_motion(g.stock_pool)
    run_daily(my_trade_prepare, time='7:00', reference_security='000300.XSHG')
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(my_sell2buy, time='9:35', reference_security='000300.XSHG')
    run_daily(check_lose, time='open', reference_security='000300.XSHG')
    run_daily(pre_hold_check, time='11:25')
    run_daily(hold_check, time='11:27')

复制
