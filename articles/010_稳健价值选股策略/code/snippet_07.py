def initialize(context):
    # 系统设置
    log.set_level('order', 'error')  # 过滤低级别日志
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option('avoid_future_data', True)  # 防止未来数据
    set_benchmark('000905.XSHG')  # 设置基准指数为中证500指数
    # 策略参数
    g.stock_num = 95  # 持仓股票数量上限
    # 设定定时运行函数
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(my_Trader, 1, time='9:30')  # 每月初进行调仓
    run_daily(check_limit_up, time='14:00')  # 每日检查涨停股票

复制
