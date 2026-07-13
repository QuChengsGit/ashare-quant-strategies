def after_code_changed(context):
    log.info('初始函数开始运行且全局只运行一次')
    unschedule_all()
    set_params()    # 设置策略参数
    set_variables() # 设置中间变量
    set_backtest()  # 设置回测条件
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 设定每天的运行时间
    run_daily(before_market_open, time='7:00')
    run_daily(call_auction, time='09:26')
    run_daily(market_run, time='14:55')

复制
