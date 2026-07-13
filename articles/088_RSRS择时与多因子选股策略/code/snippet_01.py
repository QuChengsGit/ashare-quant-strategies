def initialize(context):
    set_benchmark('399300.XSHE')  # 基准为沪深300指数
    set_option('use_real_price', True)  # 用真实价格交易
    set_option("avoid_future_data", True)  # 防止未来函数
    set_slippage(FixedSlippage(0))  # 设置固定滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5),type='fund')
    log.set_level('order', 'error')  # 只记录error级别以上的日志
    g.stock_num = 4  # 每次持仓的股票数量
    g.ref_stock = '000300.XSHG'  # 择时的基准股票（沪深300）
    g.N = 18  # 计算RSRS斜率的天数
    g.M = 600  # 计算RSRS标准分数的天数
    g.score_threshold = 0.7  # RSRS标准分数的阈值
    g.mean_day = 30  # 移动平均线的天数
    g.mean_diff_day = 2  # 移动平均线偏差天数
    g.slope_series = initial_slope_series()[:-1]  # 初始化斜率序列
    run_daily(my_trade, time='9:45', reference_security='000300.XSHG')  # 每日交易时间
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')  # 每日收盘后打印信息
