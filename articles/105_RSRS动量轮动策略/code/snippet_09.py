def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    g.stock_pool = [
        '000300.XSHG', # 沪深300
        '000905.XSHG', # 中证500
        '399006.XSHE', # 创业板
    ]
    g.momentum_day = 29
    g.N = {'000300.XSHG':18, '000905.XSHG':18, '399006.XSHE':18}
    g.M = {'000300.XSHG':700, '000905.XSHG':800, '399006.XSHE':500}
    g.score_threshold = {'000300.XSHG':0.7, '000905.XSHG':1, '399006.XSHE':0.4}
    g.max_value = None
    g.last_value = None
    g.check_out_list = None
    g.timing_signal = None
    set_order_cost(OrderCost(close_tax=0, open_commission=0.00011, close_commission=0.00011, min_commission=5), type='stock')
    set_slippage(FixedSlippage(0.001))
    run_daily(calculate, time='8:00', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(my_trade, time='11:20', reference_security='000300.XSHG')
    run_daily(my_trade, time='14:50', reference_security='000300.XSHG')

复制
