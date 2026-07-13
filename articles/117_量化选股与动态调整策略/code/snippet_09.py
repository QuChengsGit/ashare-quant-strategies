def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准指数
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 禁用未来数据
    set_option('order_volume_ratio', 1)  # 设置交易量限制
    set_slippage(PriceRelatedSlippage(0.002), type='stock')  # 设置滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=0.1), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 过滤低于error级别的日志

    g.stock_num = 9  # 持仓最大股票数
    g.limit_up_list = []  # 记录持仓中涨停的股票
    g.hold_list = []  # 当前持仓的股票
    g.history_hold_list = []  # 历史持仓记录
    g.not_buy_again_list = []  # 最近买过且涨停过的股票不再买入
    g.limit_days = 10  # 不再买入的时间段天数
    g.target_list = []  # 待操作的股票池

    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 每日准备股票池
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周调整持仓
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 检查涨停股票
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')  # 打印每日持仓信息

复制
