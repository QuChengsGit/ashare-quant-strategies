def initialize(context):
    set_params()
    set_variables()
    set_backtest()
    run_monthly(Trade, -1, time='open', reference_security='000300.XSHG')

复制
