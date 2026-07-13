def initialize(context):
    # 设定基准
    set_benchmark('000300.XSHG')  # 沪深300指数
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 设置滑点为0，适用于理论研究和回测
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, 
                            close_today_commission=0, min_commission=5), type='stock')
    # 日志配置
    log.set_level('order', 'error')
    log.set_level('system', 'error')
    # 初始化全局变量
    g.stock_num = 4  # 最大持仓数
    g.limit_up_list = []  # 记录持仓中涨停的股票
    g.hold_list = []  # 当前持仓的全部股票
    g.limit_days = 20  # 不再买入的时间段天数
    g.target_list = []  # 开盘前预操作股票池
    # 配置调度任务
    do_schedule(context)
