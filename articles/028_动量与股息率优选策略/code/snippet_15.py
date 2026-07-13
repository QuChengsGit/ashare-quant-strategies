def check_at_dayend(context):
    btlist = context.portfolio.positions
    cdata = get_current_data()
    VOLT, MAVOL5, MAVOL10 = VOL(btlist, check_date=context.current_dt, M1=5, M2=10, include_now=True)
    sell_list = []
    for stock in btlist:
        if cdata[stock].last_price != cdata[stock].high_limit and VOLT[stock] > MAVOL10[stock] * 3:
            log.info("[%s]放量未涨停，卖出" % cdata[stock].name)
            sell_list
.append(stock)
    sellstock(context, sell_list)
    buystock(context, g.buylist)

复制
