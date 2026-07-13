def initialize(context):
    # 设定中证500作为基准
    set_benchmark('000905.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 避免使用未来数据
    set_option("avoid_future_data", True)
    # 过滤掉低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 8  # 持股数量
    g.limit_days = 20  # 检查最近20天内涨停的股票
    g.hold_list = []  # 当前持仓股票列表
    g.history_hold_list = []  # 历史持仓股票列表
    g.not_buy_again_list = []  # 不再买入的股票列表
    # 设置交易时间，每天和每月运行
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(monthly_adjustment, monthday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
