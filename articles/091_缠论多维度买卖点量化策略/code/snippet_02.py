def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    g.security = '300354.XSHE'  # 设定要操作的股票
