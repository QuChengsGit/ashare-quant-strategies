set_benchmark('000300.XSHG')
set_option('use_real_price', True)
set_option("avoid_future_data", True)
log.set_level('order', 'error')
set_slippage(FixedSlippage(0.02))

复制
