def rebalance(context, stock_df):
    # 每只股票购买金额
    total_value = context.portfolio.total_value
    stock_list = stock_df['name'][int(len(stock_df) * g.quantile[0]/100) : int(len(stock_df) * g.quantile[1]/100)].tolist()
    tar_pos = total_value / len(stock_list)
    # 获取股票名称
    name_list = [get_security_info(it).display_name for it in stock_list]
    log.info(f'############## len: {len(stock_list)}, \n tar_pos: {tar_pos}, \n stock list：{str(stock_list)} \n name list: {str(name_list)} ##############')
    for k1 in context.portfolio.positions.keys():
        if k1 not in stock_list:
            order_target_value(k1, 0)  # 卖出不在新选股列表中的股票
    for k in stock_list:
        order_target_value(k, tar_pos)  # 买入新的目标股票

复制
