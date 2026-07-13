def initialize(context):
    # 设置基准指数，所有绩效以该指数为参考基准
    set_benchmark('000905.XSHG')
    # 使用真实价格进行交易
    set_option('use_real_price', True)
    # 打开防未来函数，避免使用未来数据
    set_option("avoid_future_data", True)
    # 设置滑点为0，即不考虑交易中的滑点影响
    set_slippage(FixedSlippage(0))
    # 设置交易费用，包含买卖佣金与税费
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 设置日志级别，防止输出不必要的日志信息
    log.set_level('order', 'error')
    # 初始化全局变量
    g.no_trading_today_signal = False
    g.stock_num = 1  # 每次调仓买入的股票数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票列表
    # 定义多因子模型和权重
    g.factor_list = [
        (['ARBR', 'SGAI', 'net_profit_to_total_operate_revenue_ttm', 'retained_profit_per_share'], [-0.00015, 0.0068, -0.0135, -0.0504]),
        (['Price1Y', 'total_profit_to_cost_ratio', 'VOL120'], [-1.6482, -0.1706, -0.0618]),
        (['debt_to_assets', 'operating_cost_to_operating_revenue_ratio', 'DAVOL20', 'price_no_fq', 'sales_growth'], [0.0582, -0.191, -0.2737, -0.0275, 0.1189])
    ]
    # 设置交易运行时间
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00')
    run_daily(close_account, '14:30')
    run_daily(print_position_info, '15:10')
