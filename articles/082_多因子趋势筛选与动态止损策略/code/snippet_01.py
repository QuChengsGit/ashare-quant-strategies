def after_code_changed(context):
    log.info('初始函数开始运行且全局只运行一次')
    unschedule_all()  # 取消之前所有的调度
    set_params()      # 设置策略参数
    set_variables()   # 设置中间变量
    set_backtest()    # 设置回测条件
    # 股票交易手续费设置
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 运行调度设置
    run_daily(before_market_open, time='7:00')  # 开盘前运行
    run_daily(market_open, time='09:30')        # 开盘时运行
