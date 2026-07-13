def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 设置滑点为0.004
    set_slippage(FixedSlippage(0.004))
    # 设置交易成本万分之五
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0005, close_commission=0.0005, close_today_commission=0, min_commission=5),
                   type='fund')
    # 仅记录严重错误日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.index_pool = [
        '518880.XSHG',  # 黄金ETF
        '513100.XSHG',  # 纳指100
        '159915.XSHE',  # 创业板100
        '510180.XSHG'   # 上证180
    ]
    g.stock_num = 1  # 持仓股票数量
    g.momentum_day = 25  # 动量计算窗口
    g.stock = '000300.XSHG'  # RSRS模型的标的指数
    g.N = 18  # RSRS模型参数
    g.M = 600  # RSRS模型参数
    g.mean_day = 20  # 均线天数
    g.mean_diff_day = 3  # 均线差异天数
    g.score_threshold = 0.7  # RSRS分值阈值
    g.slope_series = initial_slope_series()[:-1]  # 初始化斜率序列
    # 设置每日交易时间
    run_daily(trade, time='9:45')
