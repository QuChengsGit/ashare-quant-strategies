import pandas as pd
def initialize(context):
    # 系统设置
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_benchmark('000905.XSHG')
    # 策略参数
    g.stock_num = 95  # 持仓股票数量
    # 设置策略运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_monthly(my_Trader, 1, time='9:30')
    run_daily(check_limit_up, time='14:00')
# 主交易函数：每月进行调仓操作
def my_Trader(context):
    # 获取所有股票列表
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    # 过滤科创板和北交所股票以及ST股票
    stocks = filter_kcbj_stock(stocks)
    stocks = filter_st_stock(stocks)
    # 获取基本面数据并筛选
    df = get_fundamentals(query(
            valuation.code
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,
            indicator.inc_return > 0,
            indicator.inc_total_revenue_year_on_year > 0,
            indicator.inc_net_profit_year_on_year > 0,
            indicator.ocf_to_operating_profit > 5
        ).order_by(
            valuation.market_cap.asc()
        ).limit(g.stock_num))
    choice = list(df.code)
    # 卖出不在选择列表中的股票
    for stock in context.portfolio.positions:
        if stock not in choice and stock not in g.high_limit_list:
            order_target(stock, 0)
    # 计算每只股票的买入金额并买入新股票
    psize = context.portfolio.total_value / g.stock_num
    for stock in choice:
        if context.portfolio.available_cash < psize:
            break
        if stock not in context.portfolio.positions:
            order_value(stock, psize)
# 准备股票池，记录涨停股票
def prepare_stock_list(context):
    g.high_limit_list = []
    hold_list = list(context.portfolio.positions)
    if hold_list:
        df = get_price(hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close == high_limit and paused == 0')['code'].tolist()
# 调整昨日涨停股票的持仓情况
def check_limit_up(context):
    current_data = get_current_data()
    if g.high_limit_list:
        for stock in g.high_limit_list:
            if current_data[stock].last_price < current_data[stock].high_limit:
                log.info(f"[{stock}]涨停打开，卖出")
                order_target(stock, 0)
            else:
                log.info(f"[{stock}]涨停，继续持有")
# 过滤科创板和北交所股票
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] == '4' or stock[0] == '8' or stock[:2] == '68')]
# 过滤ST及其他具有退市标签的股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
        current_data[stock].is_st or
        'ST' in current_data[stock].name or
        '*' in current_data[stock].name or
        '退' in current_data[stock].name)]

复制
