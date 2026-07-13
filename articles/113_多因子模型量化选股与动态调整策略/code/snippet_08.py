def check_csy(context):
    if g.switch == 0:
        g.switch = g.switch + 1
    else:
        yesterday = context.previous_date
        dict_high = history(1, unit='1d', field='high', security_list=g.hold_list, df=False, skip_paused=False, fq='pre')
        dict_open = history(1, unit='1d', field='open', security_list=g.hold_list, df=False, skip_paused=False, fq='pre')
        dict_close = history(2, unit='1d', field='close', security_list=g.hold_list, df=False, skip_paused=False, fq='pre')
        for stock in g.hold_list:
            kpzf = (dict_open[stock][0] - dict_close[stock][0]) / dict_close[stock][0]
            spzf = (dict_close[stock][1] - dict_close[stock][0]) / dict_close[stock][0]
            if (kpzf - spzf) > 0.068:
                log.info("[%s]昨日大阴线，卖出" % stock)
                position = context.portfolio.positions[stock]
                close_position(position)
