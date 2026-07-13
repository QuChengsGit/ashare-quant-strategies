def set_backtest():
    set_redeem_latency(day=2, type='open_fund')  # 设置赎回到账时间
    set_option("avoid_future_data", True)  # 避免引入未来数据
    set_option("use_real_price", True)  # 使用真实价格交易
    set_benchmark('000300.XSHG')  # 设置基准
    log.set_level('order', 'error')  # 设置日志级别
