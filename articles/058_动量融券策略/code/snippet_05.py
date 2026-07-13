def after_market_close(context):
    p = context.portfolio.subportfolios[0]
    log.info('-' * 60)
    log.info('查看融资融券账户相关信息：')
    log.info('总资产：', p.total_value)
    log.info('净资产：', p.net_value)
    log.info('总负债：', p.total_liability)
    log.info('融资负债：', p.cash_liability)
    log.info('融券负债：', p.sec_liability)
    log.info('利息总负债：', p.interest)
    log.info('可用保证金：', p.available_margin)
    log.info('维持担保比例：', p.maintenance_margin_rate)
    log.info('账户所属类型：', p.type)
    log.info('##############################################################')
# 技术说明：
# 在收盘后，策略会输出融资融券账户的详细信息，包括总资产、净资产、负债情况等，以便监控账户的整体风险状况。
