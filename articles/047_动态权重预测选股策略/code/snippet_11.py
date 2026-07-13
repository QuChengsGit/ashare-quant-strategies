def initialize(context):
    g.benchmark = '000300.XSHG'
    g.wait_list = []
    g.buy = pd.Series(dtype=float)
    context.f = True
    set_benchmark(g.benchmark)
    set_option('use_real_price', True)
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0002, close_commission=0.0002, min_commission=5), type='stock')
    set_slippage(FixedSlippage(0.0))
    factor_analysis_initialize(context)
    set_stockpool(context)
    run_daily(set_stockpool, time='before_open', reference_security='000300.XSHG')
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(sell, time='14:59', reference_security='000300.XSHG')
    run_daily(buy, time='09:30', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

复制
