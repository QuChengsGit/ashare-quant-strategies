def initialize(context):
    set_benchmark('000300.XSHG')  # 设定沪深300为基准
    set_option('use_real_price', True)  # 开启真实价格模式
    set_option("avoid_future_data", True)  # 避免未来数据
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易成本
    init_cash = context.portfolio.starting_cash / 2
    set_subportfolios([
        SubPortfolioConfig(cash=init_cash, type='stock'),
        SubPortfolioConfig(cash=init_cash, type='stock'),
    ])
    g.buy_stock = 0  # 初始化每日操作股票
    g.count_days = 0  # 记录天数，以指导子仓位轮动
    g.fn = 250  # 过滤上市不足250个交易日的股票
    g.watch_days = 10  # 观察连板的持续天数
    g.code_list = ['None']  # 记录每天信号股票，去重使用
    g.count_list = []  # 记录每日最大连板数，用于计算情绪周期
    g.emo_cycle = 3  # 情绪周期长度
    g.p = 0.8  # 子账户仓位控制比例
    g.initial_cash = context.portfolio.available_cash / 2  # 每期可用总资金
    # 设置交易时间
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(get_stock_list, time='15:30', reference_security='000300.XSHG')
