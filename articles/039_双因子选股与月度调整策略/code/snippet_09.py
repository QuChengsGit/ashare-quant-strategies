def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准为中证500
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 启用防未来数据保护
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    # 初始化全局变量
    g.stock_num = 8  # 目标持股数
    g.limit_days = 20  # 检查过去20天内的涨停股票
    g.hold_list = []  # 当前持仓股票列表
    # 设置策略运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(monthly_adjustment, monthday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')

复制
