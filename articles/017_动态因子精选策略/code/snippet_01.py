def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来数据
    log.set_level('order', 'error')  # 过滤订单日志
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易手续费
    g.stock_num = 5  # 持股数
    g.limit_days = 20  # 检查最近20天内的涨停股票
    g.hold_list = []  # 已持股列表
    g.history_hold_list = []  # 历史持股列表
    g.not_buy_again_list = []  # 不再购买的股票列表
    g.switch = 0  # 开关
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 每天9:05运行
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一9:30运行
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 每天下午14:00运行
    run_daily(check_csy, time='09:30', reference_security='000300.XSHG')  # 每天早上9:30运行
