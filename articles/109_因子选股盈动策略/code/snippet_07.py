def initialize(context):
    # 设定基准指数为上证指数300
    set_benchmark('000905.XSHG')
    # 设置交易使用真实价格
    set_option('use_real_price', True)
    # 打开防止使用未来数据
    set_option("avoid_future_data", True)
    # 将滑点设置为0，即无滑点
    set_slippage(FixedSlippage(0))
    # 设置交易成本，包括开盘、平仓的手续费和印花税
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 只输出error级别的日志，避免大量无用信息
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10  # 最大持仓股票数
    g.hold_list = []  # 当前持仓股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票
    g.factor_list = [
        'ARBR',  # 情绪类因子 ARBR
        'SGAI',  # 质量类因子 销售管理费用指数
        'net_profit_to_total_operate_revenue_ttm',  # 质量类因子 净利润与营业总收入之比
        'retained_profit_per_share'  # 每股未分配利润
    ]
    # 设置交易策略运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 每天9:05执行准备股票池
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一9:30执行持仓调整
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 每天14:00检查涨停股票
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')  # 每天15:10打印持仓信息

复制
