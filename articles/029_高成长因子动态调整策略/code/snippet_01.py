def initialize(context):
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 防止未来数据泄露
    log.set_level('order', 'error')  # 设置日志级别为error
    # 设置滑点和交易成本
    set_slippage(FixedSlippage(0.02))
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0002, close_commission=0.0002, min_commission=0.01), type='stock')
    # 全局变量初始化
    g.total_stock_num = 10  # 最大持仓数量
    g.hold_list = []  # 当前持仓股票列表
    g.buy_list = []  # 需要买入的股票列表
    g.high_limit_list = []  # 昨日涨停的持仓股票
    g.limit_up_list = []  # 涨停的持仓股票
    g.history_hold_list = []  # 过去一段时间内的持仓股票列表
    g.not_buy_again_list = []  # 最近买过且涨停的股票列表
    g.limit_days = 20  # 不再买入的时间段天数
    g.is_empty_position = False  # 是否空仓信号
    # 定时任务设置
    run_daily(before_market_open, time='09:25', reference_security='000300.XSHG')
    run_weekly(market_opened, weekday=1, time='09:30', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:40', reference_security='000300.XSHG')
    run_daily(clear_account, '14:50')
