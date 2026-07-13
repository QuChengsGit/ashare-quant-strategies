def initialize(context):
    set_benchmark('000905.XSHG')  # 设置策略基准指数为中证500
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来函数数据偏差
    set_slippage(FixedSlippage(0))  # 设置滑点为0
