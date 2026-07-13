def initialize(context):
    set_benchmark('000905.XSHG')  # 设定中证500指数为基准
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 避免未来数据影响
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    g.stock_num = 10  # 最大持仓数
    g.limit_up_list = []  # 记录持仓中涨停的股票
    g.hold_list = []  # 当前持仓的全部股票
    g.history_hold_list = []  # 过去一段时间内持仓过的股票
    g.not_buy_again_list = []  # 最近买过且涨停过的股票不再买入的名单
    g.limit_days = 20  # 不再买入的时间段天数
    g.target_list = []  # 开盘前预操作的股票池
    # 自定义因子及分位值，设定多因子筛选
    g.factor1, g.P1, g.sort1 = 'net_profit_growth_rate', 0.1, False
    g.factor2, g.P2, g.sort2 = 'EBIT', 0.4, True
    g.factor3, g.P3, g.sort3 = 'roe_ttm', 1, False  # roe_ttm作为备用因子
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 准备股票池
    run_weekly(weekly_adjustment, weekday=1, time='9:30', reference_security='000300.XSHG')  # 每周一调仓
    run_daily(check_limit_up, time='14:00', reference_security='000300.XSHG')  # 检查持仓中涨停股
    run_daily(print_position_info, time='15:10', reference_security='000300.XSHG')  # 打印每日持仓信息
