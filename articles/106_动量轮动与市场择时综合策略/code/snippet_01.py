def initialize(context):
    set_benchmark('000300.XSHG')  # 设置沪深300为基准指数
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 打开防未来数据选项
    set_slippage(FixedSlippage(0.001))  # 设置滑点为0.1%
    set_order_cost(OrderCost(close_tax=0.001, close_commission=0.00015, min_commission=5), type='stock')  # 设置交易费用
    log.set_level('order', 'error')  # 设置日志等级为error，减少不必要的信息输出
