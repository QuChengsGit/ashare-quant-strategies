def initialize(context):
    """
    初始化策略参数和设置
    """
    set_benchmark('000985.XSHG')  # 设置基准指数，常见的做法是选择沪深300等代表性的指数
    set_option('use_real_price', True)  # 使用真实价格进行交易计算
    set_option("avoid_future_data", True)  # 开启防未来函数模式，防止未来数据泄漏
    set_slippage(FixedSlippage(0))  # 设置滑点为0，表示不考虑滑点
    set_order_cost(OrderCost(open_tax=0, 
                             close_tax=0.001, 
                             open_commission=0.0003, 
                             close_commission=0.0003,
                             close_today_commission=0, 
                             min_commission=5), 
                   type='stock')  # 设置交易成本，包括印花税、佣金等
    log.set_level('order', 'error')  # 设置日志输出级别为'error'，只记录严重问题
    # 初始化全局变量
    g.stock_num = 5  # 计划持有的股票数量
    g.max_hold_stocknum = 1  # 最大持有股票数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票列表
    g.num = 1  # 每次选取的行业数量
    # 设置每日和每周定时运行的任务
    run_daily(prepare_stock_list, '9:05')  # 每天9:05运行选股函数，准备股票列表
    run_weekly(weekly_adjustment, 1, '9:30')  # 每周一9:30进行持仓调整
    run_daily(check_limit_up, '14:00')  # 每天14:00检查持仓中的涨停股票是否需要卖出
