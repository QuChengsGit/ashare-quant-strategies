def set_backtest():
    if g.index == 'all':
        set_benchmark('000001.XSHG')
    else:
        set_benchmark(g.index)
    set_option('use_real_price', True)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    log.set_level('order', 'error')  # 设置日志等级
