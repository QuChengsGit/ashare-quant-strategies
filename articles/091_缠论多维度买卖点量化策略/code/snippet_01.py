def initialize(context):
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 开启动态复权模式(真实价格)
    log.info('初始函数开始运行且全局只运行一次')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易成本
    run_daily(before_market_open, time='every_bar', reference_security='000300.XSHG')  # 开盘前运行
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')  # 开盘时运行
    run_daily(after_market_close, time='every_bar', reference_security='000300.XSHG')  # 收盘后运行
