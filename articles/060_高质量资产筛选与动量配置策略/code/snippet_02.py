def my_trade(context):
    check_out_list = get_stock_list(context)  # 获取待买入股票列表
    log.info('今日准备购买的股票:%s' % check_out_list)  # 输出待买入的股票列表
    adjust_position(context, check_out_list)  # 调整持仓
