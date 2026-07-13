def initialize(context):
    g.purchases = []
    g.sells = []
    set_params()
    set_option("avoid_future_data", True)
    set_option('use_real_price', True)
    set_benchmark('000300.XSHG')
    log.set_level('order', 'error')
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.00005, close_commission=0.00005, min_commission=0), type='stock')
    run_daily(before_market_open, time='21:00', reference_security='000300.XSHG')
    run_daily(get_signal, time='21:00')
    run_daily(ETF_trade, time='9:32')

复制
