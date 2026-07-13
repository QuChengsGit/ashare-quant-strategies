from jqdata import *
def initialize(context):
    set_benchmark('000300.XSHG')  # 设置基准指数为沪深300
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 避免使用未来数据进行回测
    log.info('初始函数开始运行且全局只运行一次')
    g.stock_num = 3  # 每次持有的最大股票数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票
    g.candidate_list = []  # 候选股票列表
    g.buy1_stock_lists = []  # 早上待买入的股票列表
    g.buy2_stock_lists = []  # 中午待买入的股票列表
    # 设定交易成本
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 每周一早上运行股票池准备
    run_weekly(weekly_prepare_stock, 1, time='7:00', reference_security='000300.XSHG')
    # 每日开盘时准备当日的股票池
    run_daily(prepare_stock_list, time='9:30', reference_security='000300.XSHG')
    # 开盘时及午盘时卖出不符合条件的股票
    run_daily(my_trade_sell, time='9:30', reference_security='000300.XSHG')
    run_daily(my_trade_sell, time='13:30', reference_security='000300.XSHG')
    # 午盘时检查并卖出昨日涨停但未继续涨停的股票
    run_daily(check_limit_up, time='13:30', reference_security='000300.XSHG')
    # 午盘时买入符合条件的股票
    run_daily(my_trade_buy2, time='13:31', reference_security='000300.XSHG')
    # 收盘后记录交易信息
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

复制
