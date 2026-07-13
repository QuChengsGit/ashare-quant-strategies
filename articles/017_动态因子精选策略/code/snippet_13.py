def check_csy(context):
    target_list = list(context.portfolio.positions)
    st_list = get_st_stock()
    for stock in target_list:
        if stock in st_list:
            log.info("[%s]为ST股，卖出" % stock)
            position = context.portfolio.positions[stock]
            close_position(position)

复制
