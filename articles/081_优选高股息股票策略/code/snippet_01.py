def initialize(context):
    # 设定基准
    set_benchmark('510880.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    log.set_level('system', 'error')
    # 设置股票数量
    g.stocknum = 30
    # 每月调仓
    run_monthly(trade, 1, '10:00')
