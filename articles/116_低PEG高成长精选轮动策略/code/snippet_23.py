run_daily(before_market_open, time='09:25', reference_security='000300.XSHG')
run_weekly(market_opened, weekday=1, time='09:30', reference_security='000300.XSHG')
run_daily(check_limit_up, time='14:40', reference_security='000300.XSHG')
run_daily(clear_account, time='14:50')
