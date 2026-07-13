def iReport(context):
    g.days = g.days + 1
    log.info('positions', len(context.portfolio.positions))
    log.info('return %.2f', 100*context.portfolio.returns)
    log.info('cash %.2f', context.portfolio.available_cash/10000)
    log.info('value %.2f', context.portfolio.total_value/10000)
    log.info('running days', g.days)
