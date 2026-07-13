def initialize(context):
    set_params(context)
    set_variables()
    set_backtest()
    run_daily(TradeFunc, time='10:30', reference_security='000300.XSHG')
