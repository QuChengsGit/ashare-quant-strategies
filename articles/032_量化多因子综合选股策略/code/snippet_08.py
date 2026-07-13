def initialize(context):
    # 设置系统参数
    set_option('use_real_price', True)
    set_slippage(PriceRelatedSlippage(0.00))
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 初始化全局变量
    g.chosen_stock_list = []  # 选出的股票列表
    g.sold_stock = {}         # 已卖出股票列表
    g.buy_stock_count = 4      # 购买股票数量
    g.score = 7               # 股票评分阈值
    g.buyrank = g.buy_stock_count * 2  # 输出可买入列表的个数
    g.sellrank = g.buy_stock_count * 2 # 筛选时保留的股票个数
    g.stock_selection_percent = 0.7  # 设置选取市值最大股票的百分比
    g.volume_days = 5         # 成交量计算天数
    g.increase_days = 60      # 涨幅计算天数
    g.score_weights = [2, 1, 1, 4, 4]  # 股票评分权重
    # 设置定时任务
    run_monthly(before_trading, 1, '09:29')
    run_daily(mysell, '09:30')
    run_daily(mybuy, '09:31')
    # 设置日志级别
    log.set_level('order', 'error')
    log.set_level('system', 'error')
    log.set_level('history', 'error')

复制
