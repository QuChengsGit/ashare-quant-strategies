def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 防止未来函数
    set_option("avoid_future_data", True)
    # 输出日志配置
    log.set_level('order', 'error')
    # 股票池及参数设置
    g.buy_stock_count = 5
    g.check_out_lists = []
    # 设置交易成本
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.00012, close_commission=0.00012, min_commission=5), type='stock')
    # 定时任务
    run_monthly(before_market_open, 1, time='5:00', reference_security='000300.XSHG')
    run_monthly(my_trade, 1, time='9:30', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
