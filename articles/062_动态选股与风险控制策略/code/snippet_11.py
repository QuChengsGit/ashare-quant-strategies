def add_hold_info(stock):
    g.hold_days[stock] = 0
def del_hold_info(stock):
    g.hold_days.pop(stock)
def change_hold_info(context):
    for stock in g.hold_days.keys():
        g.hold_days[stock] += 1
        log.info("%s 持股天数%s" % (stock, g.hold_days[stock]))

复制
