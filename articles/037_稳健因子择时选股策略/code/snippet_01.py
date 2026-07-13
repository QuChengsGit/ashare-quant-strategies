def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准为中证500
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 防未来函数
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志输出等级
    # 初始化全局变量
    g.stock_num = 10  # 最大持仓数量
    g.limit_days = 20  # 持有天数限制
    g.limit_up_list = []  # 涨停股列表
    g.hold_list = []  # 当前持仓列表
    g.history_hold_list = []  # 历史持仓列表
    g.not_buy_again_list = []  # 不再买入的股票列表
    # 调度交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_daily(daily_adjustment, time='9:40', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')
