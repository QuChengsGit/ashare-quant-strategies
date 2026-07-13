def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    # 全局变量初始化
    g.sel_stock = None
    g.strategy_starttime = time(10, 20)  # 策略开始买卖时间
    g.strategy_endtime = time(14, 55)    # 策略尾盘撮合买入时间
    # 交易费用设置：买入时万分之二点五，卖出时万分之二点五加千分之一印花税
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.00025, close_commission=0.00025, min_commission=5), type='stock')
    # 定时任务设置
    run_weekly(weekly, weekday=1, time='09:31', reference_security='000300.XSHG')
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

复制
