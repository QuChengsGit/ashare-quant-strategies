def initialize(context):
    # 设定基准
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 设置滑点为理想情况
    set_slippage(PriceRelatedSlippage(0.00))
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5),type='stock')
    # 初始化全局变量
    g.stock_num = 50  # 最大持仓数量
    g.high_limit_list = []  # 昨日涨停股票列表
    g.hold_list = []  # 当前持仓股票列表
    g.weights = [1.0, 1.0, 1.6, 0.8, 2.0]  # 因子权重
    g.black_list = []  # 风险黑名单
    # 设置定时任务
    run_daily(prepare_stock_list, '9:05')
    run_daily(get_black_list, '9:05')  # 获取风险黑名单
    run_weekly(adjust_position, 1, '09:30')
    run_daily(check_limit_up, '14:00')

复制
