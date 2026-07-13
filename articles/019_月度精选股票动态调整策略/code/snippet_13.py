def initialize(context):
    set_benchmark('000300.XSHG') # 设置基准指数
    log.set_level('order', 'error') # 设置日志等级为仅记录错误
    set_option('use_real_price', True) # 使用真实价格进行交易
    set_option('avoid_future_data', True) # 避免未来数据
    set_slippage(FixedSlippage(0.02)) # 设置固定滑点为0.02
    g.stock_num = 10 # 目标持股数量
    g.month = context.current_dt.month - 1 # 当前月份

复制
