def initialize(context):
    # 设置系统参数
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_benchmark('000300.XSHG')
    # 设置交易参数
    set_slippage(FixedSlippage(0.02))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    # 初始化全局变量
    g.no_trading_today_signal = False
    g.stock_num = 10
    g.choice = []
    g.just_sold = []
    g.limit_days = 30
    g.hold_list = []
    g.history_hold_list = []
    g.not_buy_again_list = []
    # 调度任务
    run_daily(prepare_high_limit_list, time='9:05', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00')
    run_monthly(my_Trader, -1, time='9:30', force=True)
    run_monthly(go_Trader, -1, time='14:55', force=True)
    run_daily(close_account, '14:30')
