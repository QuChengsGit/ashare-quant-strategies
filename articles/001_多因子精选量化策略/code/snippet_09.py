def initialize(context):
    # 设定基准指数为中证500指数
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 启用防未来函数，避免未来数据干扰策略
    set_option("avoid_future_data", True)
    # 设置滑点为0，模拟理想交易环境
    set_slippage(FixedSlippage(0))
    # 设置交易成本，考虑买卖佣金和税率
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 过滤低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.no_trading_today_signal = False
    g.stock_num = 1  # 默认持有股票数量为1
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 昨日涨停的股票列表
    # 多因子模型因子及权重
    g.factor_list = [
        (['ARBR', 'SGAI', 'net_profit_to_total_operate_revenue_ttm', 'retained_profit_per_share'],
         [-2.3425, -694.7936, -170.0463, -1362.5762]),
        (['Price1Y', 'total_profit_to_cost_ratio', 'VOL120'],
         [-0.0647128120839873, -0.006385116279168804, -0.0029867925845833217]),
        (['price_no_fq', 'total_profit_to_cost_ratio', 'inventory_turnover_rate'],
         [-6.123355346008858e-05, -0.002579342458393642, -2.194257357346814e-06]),
        (['debt_to_assets', 'operating_cost_to_operating_revenue_ratio', 'DAVOL20', 'price_no_fq', 'sales_growth'],
         [0.04477354820057883, 0.021636407482421707, -0.01864268317469762, -0.0004678118383947827, 0.02884867440332058]),
        (['TVSTD6', 'cashflow_per_share_ttm', 'sharpe_ratio_120', 'non_operating_net_profit_ttm'],
         [-5.394060941494863e-12, 4.6306072704138405e-05, -0.0030567075906980912, 1.4227113275455325e-12])
    ]
    # 设置定时任务
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00')
    run_daily(close_account, '14:30')
    run_daily(print_position_info, '15:10')

复制
