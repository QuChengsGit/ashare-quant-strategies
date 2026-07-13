def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 避免使用未来数据
    set_option("avoid_future_data", True)
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    # 过滤order中低于error级别的日志
    log.set_level('order', 'error')
    # 策略参数
    g.stock_num = 10  # 持仓数量
    g.day_count = 91  # 动量计算天数
    g.stock_price = 5  # 股价筛选条件
    # 每日开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    # 每日开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    # 每日收盘后打印交易信息
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')

复制
