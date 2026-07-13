def initialize(context):
    # 设置滑点为0.02
    set_slippage(FixedSlippage(0.02))
    # 将国证A指数作为基准
    set_benchmark('399317.XSHE')
    # 使用真实价格交易
    set_option('use_real_price', True)
    # 避免未来数据
    set_option("avoid_future_data", True)
    # 过滤低于error级别的日志
    log.set_level('order', 'error')
    warnings.filterwarnings("ignore")
    # 全局变量设置
    g.stock_num = 10  # 最大持仓数
    g.position = 1  # 仓位比例
    g.bond = '511880.XSHG'  # 债券基金代码
    # 设置交易手续费
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0005, close_commission=0.0005, min_commission=5), type='stock')
    # 每月定期交易
    run_monthly(my_trade, monthday=-4, time='11:30', reference_security='000852.XSHG')
