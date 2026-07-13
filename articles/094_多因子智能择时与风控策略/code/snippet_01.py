def initialize(context):
    set_option('use_real_price', True)
    log.set_level('order', 'error')
    log.set_level('history', 'error')
    myscheduler()
    g.isbull = False  # 是否牛市
    g.chosen_stock_list = []  # 存储选出来的股票
    g.nohold = True  # 空仓专用信号
    g.sold_stock = {}  # 近期卖出的股票及卖出天数
