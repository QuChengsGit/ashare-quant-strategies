def initialize(context):
    # 系统参数设置
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')
    # 策略参数设置
    g.stock_num = 5  # 持仓数
    g.no_trading_today_signal = False
    g.hold_list = []  # 当前持仓列表
    # 调度任务
    run_weekly(my_trade, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(close_account, '14:30')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
