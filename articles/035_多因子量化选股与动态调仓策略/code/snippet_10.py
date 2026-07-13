def initialize(context):
    # 设定基准指数为中证500
    set_benchmark('000905.XSHG')
    # 设定交易使用真实价格
    set_option('use_real_price', True)
    # 防止未来函数
    set_option("avoid_future_data", True)
    # 设置交易量限制
    set_option('order_volume_ratio', 1)
    # 设置滑点
    set_slippage(PriceRelatedSlippage(0.002), type='stock')
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=0.1), type='fund')
    # 过滤低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 9  # 最大持仓数
    g.limit_up_list = []  # 记录持仓中涨停的股票
    g.hold_list = []  # 当前持仓股票列表
    g.history_hold_list = []  # 过去持仓过的股票
    g.not_buy_again_list = []  # 不再买入的股票列表
    g.limit_days = 10  # 不再买入的时间段天数
    g.target_list = []  # 每日操作的目标股票列表
    # 设置交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')

复制
