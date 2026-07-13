from jqdata import *
# 初始化函数
def initialize(context):
    # 设置持股数量
    g.stocknum = 10
    # 初始化待买入股票列表
    g.buylist = []
    # 设置沪深300股指作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式（使用真实价格）
    set_option('use_real_price', True)
    # 交易量不超过实际成交量的 10%
    set_option('order_volume_ratio', 0.1)
    # 设置滑点（0.02 的滑点）
    set_slippage(FixedSlippage(0.02))
    # 设置交易费用
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 过滤掉 order 系列 API 产生的比 error 级别低的日志
    log.set_level('order', 'error')
    # 设置定时任务
    run_daily(stoploss, '9:45')  # 止损函数
    run_weekly(filter_stocks, 1, '09:30')  # 每周一筛选股票
    run_weekly(market_open, 1, '10:00')  # 每周一进行调仓
# 筛选、排序股票，生成待交易股票列表
def filter_stocks(context):
    log.info(f'函数运行时间（filter_stocks）: {context.current_dt.time()}')
    # 获取当前的市场数据
    curr_data = get_current_data()
    # 获取上证综指和深证综指的成份股
    stock_universe = get_index_stocks('000001.XSHG') + get_index_stocks('399106.XSHE')
    # 过滤开盘涨停、跌停、暂停交易及ST、退市股票
    stock_universe = [stock for stock in stock_universe if not (
            (curr_data[stock].day_open == curr_data[stock].high_limit) or
            (curr_data[stock].day_open == curr_data[stock].low_limit) or
            curr_data[stock].paused or
            ('ST' in curr_data[stock].name) or
            ('*' in curr_data[stock].name) or
            ('退' in curr_data[stock].name)
    )]
    # 获取市值最小的股票列表
    q = query(valuation.code, valuation.market_cap).filter(
        valuation.code.in_(stock_universe)).order_by(
        valuation.market_cap.asc()).limit(g.stocknum)
    # 获取前一个交易日的股票数据
    df = get_fundamentals(q, date=context.previous_date)
    # 将待买入股票列表赋值给全局变量
    g.buylist = list(df['code'])
# 止损函数
def stoploss(context):
    for stock in context.portfolio.positions:
        cost = context.portfolio.positions[stock].avg_cost
        price = context.portfolio.positions[stock].price
        ret = price / cost - 1
        # 如果亏损超过 20%，执行止损
        if ret < -0.2:
            order_target(stock, 0)
            log.info(f'触发止损，卖出 {stock}')
# 开盘时运行函数
def market_open(context):
    log.info(f'函数运行时间（market_open）: {context.current_dt.time()}')
    if not g.buylist:
        return
    # 调整持仓
    rebalance(context, g.buylist)
# 调仓函数
def rebalance(context, buylist):
    every_stock = context.portfolio.portfolio_value / len(buylist)
    # 如果没有持仓，直接均等买入
    if not context.portfolio.positions:
        for stock_to_buy in buylist:
            order_target_value(stock_to_buy, every_stock)
    else:
        # 先卖出不在买入列表中的股票
        for stock_to_sell in list(context.portfolio.positions.keys()):
            if stock_to_sell not in buylist:
                order_target_value(stock_to_sell, 0)
        # 调整持仓中的股票，重新分配仓位
        for stock in buylist:
            order_target_value(stock, every_stock)
