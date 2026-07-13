def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000002.XSHG')  # 沪深300指数
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 设置股票交易的费用：买入万分之三，卖出万分之三加千分之一印花税，最低每笔5元
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 初始化全局变量，获取中证全指的成分股作为初始股票池
    g.security = get_index_stocks('000985.XSHG')  # 中证全指
    g.q = query(valuation, indicator).filter(valuation.code.in_(g.security))  # 查询财务数据
    # 每周一运行选股和交易逻辑
    run_weekly(period, weekday=1)
