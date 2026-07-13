def after_market_close(context):
    log.info(f"函数运行时间(after_market_close): {str(context.current_dt.time())}")
    trades = get_trades()
    for _trade in trades.values():
        log.info(f"成交记录：{str(_trade)}")
    log.info('一天结束')
    log.info('##############################################################')
