def initialize(context):
    # 系统设置
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    # 策略调度
    run_daily(handle_training, 'before_open')
    run_daily(handle_trader, 'open')
