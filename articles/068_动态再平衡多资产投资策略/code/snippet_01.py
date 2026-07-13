def initialize(context):
    log.set_level('order', 'error')  # 过滤掉低于error级别的日志
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option('avoid_future_data', True)  # 避免未来数据影响
    run_daily(iUpdate, time='10:00')  # 每天10点更新策略
