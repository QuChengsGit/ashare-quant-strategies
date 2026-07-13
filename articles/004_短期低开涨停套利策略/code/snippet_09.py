def initialize(context):
    # 系统设置
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option('avoid_future_data', True)  # 防止未来数据干扰
    log.set_level('system', 'error')  # 过滤系统日志，避免过多冗余信息
    # 每日调度任务
    run_daily(buy, '09:30')  # 开盘后进行选股和买入操作
    run_daily(sell, '11:28')  # 上午卖出操作
    run_daily(sell, '14:50')  # 下午卖出操作

复制
