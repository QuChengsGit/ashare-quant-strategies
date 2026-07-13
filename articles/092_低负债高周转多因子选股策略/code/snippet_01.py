def initialize(context):
    set_slippage(FixedSlippage(0.02))  # 设置滑点
    set_benchmark('399317.XSHE')  # 设定国证A指数作为基准
    set_option('use_real_price', True)  # 开启真实价格交易
    set_option("avoid_future_data", True)  # 避免未来数据
    log.set_level('order', 'error')  # 设置日志级别
    warnings.filterwarnings("ignore")  # 忽略警告
    g.stock_num = 10  # 持仓股票数
    g.position = 1  # 仓位
    g.bond = '511880.XSHG'  # 债券标的
    # 设置交易成本
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0005, close_commission=0.0005, min_commission=5), type='stock')
    # 每月定期调仓
    run_monthly(my_trade, monthday=-4, time='11:30', reference_security='000852.XSHG')
