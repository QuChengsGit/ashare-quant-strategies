from jqdata import *
def initialize(context):
    log.set_level('order', 'warning')  # 设置日志级别
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 避免未来数据
    set_slippage(FixedSlippage(0.02))  # 固定滑点设置
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')  # 设置交易成本
    set_benchmark('399303.XSHE')  # 设置基准指数为中证500指数
    g.choice = 500  # 选择前500只股票
    g.stock_num = 5  # 最大持仓股票数量
    g.stock_pool = []  # 股票池
    run_daily(my_trade, time='9:30', reference_security='399303.XSHE')  # 每天9:30运行交易函数

复制
