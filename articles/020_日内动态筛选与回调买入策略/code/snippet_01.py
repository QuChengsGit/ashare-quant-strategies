def initialize(context):
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    set_slippage(FixedSlippage(0.02))  # 设置滑点
    set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))  # 设置交易佣金
    set_benchmark('399303.XSHE')  # 设置基准指数
    g.choice = 500  # 股票池大小
    g.amount = 7  # 最大持仓股票数量
    g.muster = []  # 筛选后的股票列表
    g.bucket = []  # 备选股票列表
    g.summit = {}  # 存储其他信息
    log.set_level('order', 'warning')  # 设置日志级别
    run_daily(buy, time='9:30', reference_security='399303.XSHE')  # 每日9:30执行买入
    run_daily(sell, time='10:30', reference_security='399303.XSHE')  # 每日10:30执行卖出
