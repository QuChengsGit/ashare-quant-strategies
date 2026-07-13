def initialize(context):
    # 设定基准指数为中证500
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 防止未来数据的使用
    log.set_level('order', 'error')  # 仅记录error级别的日志
    # 初始化全局变量
    g.stock_num = 10  # 持仓股票数
    g.limit_days = 20  # 涨停后避免重新买入的天数
    g.hold_list = []  # 当前持仓列表
    g.history_hold_list = []  # 历史持仓记录
    g.not_buy_again_list = []  # 涨停后避免买入的股票列表
    # 设定每日、每周的运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')

复制
