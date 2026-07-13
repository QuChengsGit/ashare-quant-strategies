def initialize(context):
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')
    # 选股参数
    g.stock_num = 5  # 持仓数
    # 设置交易时间，每周一运行
    run_weekly(print_stock_list_before_open, weekday=1, time='9:15', reference_security='000300.XSHG')
    run_weekly(my_trade, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')

复制
