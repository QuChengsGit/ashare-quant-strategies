def initialize(context):
    set_benchmark('000905.XSHG')  # 设置基准指数为中证500指数
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志级别为错误，过滤低级别日志
    # 初始化全局变量
    g.stock_num = 10  # 设置最大持仓数为10
    g.limit_up_list = []  # 用于记录涨停的股票
    g.hold_list = []  # 当前持仓股票
    g.history_hold_list = []  # 记录过去持仓的股票
    g.not_buy_again_list = []  # 不再买入的股票列表
    g.limit_days = 20  # 设置不再买入股票的时间段为20天
    g.target_list = []  # 预操作股票池
    g.industry_control = True  # 是否过滤不看好的行业
    g.industry_filter_list = ['钢铁I','煤炭I','石油石化I','采掘I', '银行I','非银金融I','金融服务I', '交运设备I','交通运输I','传媒I','环保I']  # 不看好的行业列表
