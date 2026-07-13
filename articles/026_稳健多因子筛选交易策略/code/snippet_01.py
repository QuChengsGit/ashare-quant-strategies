def initialize(context):
    log.set_level('order', 'error')  # 过滤掉低于error级别的log
    set_option('use_real_price', True)  # 开启动态复权模式
    set_option('avoid_future_data', True)  # 避免未来数据
    set_option('order_volume_ratio', 0.1)  # 交易量不超过实际成交量的10%
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_slippage(PriceRelatedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易成本
    g.stock_num = 20  # 最大持仓股票数量
    g.buylist = []  # 待买入股票列表
    g.high_limit_list = []  # 昨日涨停股票列表
    # 设定定时任务
    run_daily(get_high_limit, time='9:00')  # 每天早上获取昨日涨停股票
    run_monthly(get_stocks, 1, time='10:00')  # 每月第一个交易日筛选股票
    run_monthly(trade_stocks, 1, time='14:55')  # 每月第一个交易日执行交易
    run_monthly(show_cap, 1, time='16:00')  # 每月第一个交易日收盘后输出市值等信息
    run_daily(check_high_limit, time='14:40')  # 每日下午检查昨日涨停股票
