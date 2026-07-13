def do_schedule(context):    
    # 设置交易运行时间
    run_daily(get_stock_list, time='8:00', reference_security='000300.XSHG')  # 选股
    run_daily(prepare_trade, time='8:05', reference_security='000300.XSHG')  # 准备交易
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 检查涨停
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一调仓
    run_weekly(print_position_info, weekday=1, time='15:10', reference_security='000300.XSHG')  # 每周一打印持仓信息
