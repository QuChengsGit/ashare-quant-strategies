def initialize(context):
    set_benchmark('399317.XSHE')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 用真实价格交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    set_slippage(FixedSlippage(0.02))  # 设置滑点为0.02
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0005, close_commission=0.0005, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('system', 'error')  # 过滤低于error级别的日志
    g.index_pool = ['000016.XSHG', '399303.XSHE']  # 指数池
    g.momentum_day = 89  # 动量计算的时间窗口
    g.position = 1  # 仓位
    g.stock_num = 10  # 大盘股持仓数量
    g.stock_num_small = 30  # 小盘股持仓数量
    run_monthly(my_sell, monthday=-10, time='11:00', reference_security='399317.XSHE')  # 卖出操作
    run_monthly(my_buy, monthday=-1, time='11:15', reference_security='399317.XSHE')  # 买入操作
