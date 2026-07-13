def set_backtest():
    set_option("avoid_future_data", True)
    set_option("use_real_price", True)
    set_benchmark('000300.XSHG')
    log.set_level('order', 'error')

复制
