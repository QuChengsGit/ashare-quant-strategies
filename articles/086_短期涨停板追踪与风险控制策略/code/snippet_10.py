def set_run_daily():
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(Call_auction, time='09:25', reference_security='000300.XSHG')
    run_daily(market_open_sell_buy, time='every_bar', reference_security='000300.XSHG')
    run_daily(before_closing, time='14:55', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

复制
