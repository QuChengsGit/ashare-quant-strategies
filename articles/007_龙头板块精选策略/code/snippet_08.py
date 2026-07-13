def initialize(context):
    # 使用真实价格交易
    set_option('use_real_price', True)
    # 防止未来数据
    set_option('avoid_future_data', True)
    # 设定日志级别，仅保留error级别以上的日志
    log.set_level('system', 'error')
    # 设置最大持仓数量
    g.ps = 10  # 同时持有的最高龙头股数量
    # 设定筛选因子
    g.jqfactor = 'VOL5'  # 5日平均换手率
    g.sort = True  # 按因子值从小到大排序
    # 每日调度任务
    run_daily(get_stock_list, '9:01')
    run_daily(buy, '09:30')
    run_daily(sell, '14:50')
    run_daily(print_position_info, '15:02')

复制
