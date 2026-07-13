def initialize(context):
    set_benchmark('511010.XSHG')  # 基准设为上证国债ETF
    set_option('use_real_price', True)  # 用真实价格交易
    log.set_level('order', 'error')  # 只记录error级别以上的日志
    set_slippage(FixedSlippage(0.002))  # 设置滑点
    g.transactionRecord, g.trade_ratio, g.positions = {}, {}, {}  # 初始化交易记录、交易比例、持仓记录
    g.hold_periods, g.hold_cycle = 0, 30  # 持仓周期设定为30天
    g.QuantLib = QuantLib()  # 初始化量化库实例
    # 设定每日交易的时间点
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
