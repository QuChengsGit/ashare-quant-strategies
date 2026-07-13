def clear_close(context):
    log.info('开始融券卖出...')
    # 获取全市场可融券标的
    security = get_marginsec_stocks(date=context.current_dt)
    current_data = get_current_data()
    zf_dict = {}
    for s in security:
        cc = get_bars(s, count=2, unit='1d', fields=['high', 'low', 'close'], include_now=True)
        if not current_data[s].paused and len(cc['close']) == 2:
            zf = (cc['high'][-1] - cc['low'][-1]) / cc['close'][0] * 100
            if (cc['high'][-1] - cc['low'][-1]) / (current_data[s].high_limit - cc['close'][0]) > 1.5:
                zf_dict[s] = zf
    # 对波动率进行排序，选择波动率最高的股票进行融券卖出
    dm = sorted(zf_dict.items(), key=lambda x: x[1], reverse=True)
    g.buylist0 = [s[0] for s in dm][:10]
    log.info('融券卖出: %s' % g.buylist0)
    if g.buylist0:
        position_per_money = context.portfolio.total_value / len(g.buylist0)
        for stock in g.buylist0:
            current_price = get_bars(stock, count=1, unit='5m', fields=['close'], include_now=True)['close'][-1]
            position_per_money_n = int(position_per_money / current_price / 100) * 100
            log.info("融券卖出: %s" % [stock, current_price, position_per_money_n])
            marginsec_open(stock, position_per_money_n)
# 技术说明：
# 在尾盘时，策略会对全市场可融券标的进行波动率筛选，选择波动率较大的股票进行融券卖出。卖出数量根据总资产按比例分配。
