def initialize(context):
    enable_profile()  # 启用性能分析
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 开启动态复权模式(真实价格)
    set_option("avoid_future_data", True)  # 关闭未来函数
    set_slippage(FixedSlippage(0))  # 将滑点设置为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本万分之三
    g.buy_stock_limit = 1  # 股票购买限制，设置为1表示每次只买入1支股票

复制
