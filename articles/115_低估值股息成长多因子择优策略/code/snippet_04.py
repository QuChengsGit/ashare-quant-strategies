def show_cap(context):
    current_data = get_current_data()
    log.info("当前持仓市值：")
    for stock, position in context.portfolio.positions.items():
        log.info("{}：市值 {:.2f} 元，现价 {:.2f}".format(
            stock, position.value, current_data[stock].last_price))
