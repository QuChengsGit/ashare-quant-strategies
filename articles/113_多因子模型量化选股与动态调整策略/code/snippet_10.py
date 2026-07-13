def initialize(context):
    # 设定基准
    set_benchmark('000905.XSHG')  # 设置上证180指数作为基准
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    log.set_level('order', 'error')  # 设置日志等级为error，避免日志干扰
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易手续费
    # 初始化全局变量
    g.stock_num = 5  # 持股数量
    g.limit_days = 20  # 检查过去20天内是否涨停
    g.hold_list = []  # 持仓列表
    g.history_hold_list = []  # 历史持仓列表
    g.not_buy_again_list = []  # 最近买过的股票列表
    g.switch = 0  # 开关变量
    # 设置交易时间，每天执行
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    # 每周执行：获取并调整持仓股票
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')
    # 每日执行：检查涨停股票
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')
    # 每日执行：检查长上影线股票
    run_daily(check_csy, time='09:30', reference_security='000300.XSHG')

复制
