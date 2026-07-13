def initialize(context):
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='fund')
    log.set_level('order', 'error')
    g.stock_num = 10  # 最大持仓数
    g.limit_days = 20  # 保持一定周期内的持仓记录
    g.limit_up_list = []  # 涨停股票列表
    g.hold_list = []  # 当前持仓股票
    g.history_hold_list = []  # 历史持仓记录
    g.not_buy_again_list = []  # 不再买入的股票列表
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')

复制
