def initialize(context):
    set_benchmark('000905.XSHG')  # 设定基准为中证500指数
    set_option('use_real_price', True)  # 用真实价格交易
    set_option("avoid_future_data", True)  # 启用防未来数据
    set_slippage(PriceRelatedSlippage(0.000))  # 设置理想滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    g.stock_num = 50  # 目标持仓股票数量
    g.limit_up_list = []  # 涨停股票列表
    g.hold_list = []  # 当前持仓列表
    g.weights = [1.0, 1.0, 1.6, 0.8, 2.0]  # 各因子的权重
    # 设置交易时间和任务调度
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')

复制
