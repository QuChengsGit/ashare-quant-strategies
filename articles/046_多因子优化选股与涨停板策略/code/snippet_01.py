def initialize(context):
    # 设置基准为中证500指数
    set_benchmark('000905.XSHG')
    # 启用真实价格交易模式，避免未来数据
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    # 设置滑点为0，交易成本为0.03%
    set_slippage(FixedSlippage(0))
    set_option('order_volume_ratio', 0.1)
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 设置日志级别为只显示error及以上级别日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10  # 最大持仓数量
    g.limit_days = 20  # 股票交易间隔限制
    g.high_limit_list = []  # 昨日涨停股列表
    g.hold_list = []  # 当前持仓列表
    g.history_hold_list = []  # 历史持仓记录
    g.not_buy_again_list = []  # 限制买入列表
    # 设置交易时间和频率
    run_daily(prepare_stock_list, time='9:00')
    run_weekly(weekly_adjustment, weekday=1, time='09:40')
    run_daily(check_limit_up, time='14:00')
    run_daily(print_position_info, time='15:30')
