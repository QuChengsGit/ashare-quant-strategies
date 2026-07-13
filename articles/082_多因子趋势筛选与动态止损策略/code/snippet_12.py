def set_backtest():
    set_benchmark(g.index)  # 设定基准指数
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    log.set_level('order', 'error')  # 设置报错等级

复制
