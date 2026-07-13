def initialize(context):
    # 设置基准指数为中证500
    set_benchmark('000905.XSHG')
    # 使用真实价格进行交易
    set_option('use_real_price', True)
    # 启用防未来数据功能
    set_option("avoid_future_data", True)
    # 设置滑点为0，表示没有滑点
    set_slippage(FixedSlippage(0))
    # 设置交易成本：开盘时无税，闭盘时每笔交易万分之三，最小佣金5元
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 设置日志过滤级别，过滤低于error级别的日志
    log.set_level('order', 'error')
    log.set_level('system', 'error')
    # 初始化全局变量
    g.no_trading_today_signal = False  # 是否为停止交易信号
    g.stock_num = 3  # 每次持仓的股票数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 昨日涨停股票列表
    # 设置因子列表和选择的因子
    g.factor_list = [{'ARBR': (-0.9996444781983547, 0.9986148448690932)}]
    g.chosen_factor = ['ARBR']  # 选定使用的因子
    g.month_day = 1  # 每月的交易日
    # 设置策略运行时间
    run_daily(prepare_stock_list, '9:05')  # 每天9:05准备股票池
    run_weekly(weekly_adjustment, g.month_day, '9:30')  # 每周调整持仓，设定为每月第1个交易日
    run_daily(check_limit_up, '14:00')  # 每天14:00检查持仓中是否有涨停股需要卖出
    run_daily(close_account, '14:30')  # 每天14:30进行资金清算

复制
