def after_market_close(context):
    positions_dict = context.portfolio.positions
    for position in list(positions_dict.values()):
        log.info("当前持仓:{0}, 数量:{1}, 市值:{2}, 盈利：{3}%, 建仓时间:{4}".format(
            get_name(position.security), position.total_amount, round(position.value, 0),
            round((position.value - (position.avg_cost * position.total_amount)) /
                  (position.avg_cost * position.total_amount) * 100, 1),
            position.init_time))
    log.info('#########################################################################################\n\n')
