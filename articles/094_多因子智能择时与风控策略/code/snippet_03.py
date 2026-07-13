def get_growth_rate(code, n=20):
    lc = get_close_price(code, n)
    c = get_close_price(code, 1, '1m')
    if not isnan(lc) and not isnan(c) and lc != 0:
        return (c - lc) / lc
    else:
        log.error("数据非法, code: %s, %d日收盘价: %f, 当前价: %f" % (code, n, lc, c))
        return 0
