def initialize(context):
    # 设定基准
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 过滤order中低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.no_trading_today_signal = False
    g.stock_num = 1
    g.hold_list = []  # 当前持仓的全部股票    
    g.yesterday_HL_list = []  # 记录持仓中昨日涨停的股票
    # 定义因子与对应的系数
    g.factor_list = [
        # 因子组合1
        ([
            'ARBR', # 情绪类因子
            'SGAI', # 销售管理费用指数
            'net_profit_to_total_operate_revenue_ttm', # 净利润与营业总收入之比
            'retained_profit_per_share' # 每股未分配利润
        ], [
            -0.00015399364219672028,
            0.0068040696770965275,
            -0.013582394749579795,
            -0.05043296392026463
        ]),
        # 因子组合2
        ([
            'Price1Y', # 动量类因子
            'total_profit_to_cost_ratio', # 成本费用利润率
            'VOL120' # 120日平均换手率
        ], [
            -1.6481969388084845,
            -0.17062057099935446,
            -0.061842557079243125
        ]),
        # 因子组合3
        ([
            'debt_to_assets', # 资产负债率
            'operating_cost_to_operating_revenue_ratio', # 销售成本率
            'DAVOL20', # 20日平均换手率与120日平均换手率之比
            'price_no_fq', # 不复权价格因子
            'sales_growth' # 5年营业收入增长率
        ], [
            0.058175841938529524,
            -0.1910332189773409,
            -0.2736912625714264,
            -0.027468330345688075,
            0.11887746662741136
        ])
    ]
    # 设置交易运行时间
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00') #检查持仓中的涨停股是否需要卖出
    run_daily(close_account, '14:30')
    run_daily(print_position_info, '15:10')
