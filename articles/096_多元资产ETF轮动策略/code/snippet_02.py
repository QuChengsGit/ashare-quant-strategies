def set_params():
    g.target_market = '000300.XSHG'
    g.moment_period = 13  # 计算行情趋势的短期均线周期
    g.ma_period = 10      # 计算均线的周期
    g.type_num = 5        # 每次最多选择的资产类别数量
    g.ETF_targets = {
        '000300.XSHG':'510300.XSHG',  # 沪深300
        '399006.XSHE':'159915.XSHE',  # 创业板
        '518880.XSHG':'518880.XSHG',  # 黄金ETF
        '501018.XSHG':'501018.XSHG',  # 南方原油
        '161226.XSHE':'161226.XSHE',  # 白银基金
        # 更多标的...
    }
    g.local_stocks  = ['510300.XSHG', '159915.XSHE']
    g.global_stocks = ['513100.XSHG', '164824.XSHE']
    g.local_futures = ['159980.XSHE', '159981.XSHE']
    g.global_futures = ['161226.XSHE', '518880.XSHG']
    g.REITs = ['180101.XSHE', '180301.XSHE']
    # 打印股票池信息
    stocks_info = "\n股票池:\n"
    for security in g.ETF_targets.values():
        s_info = get_security_info(security)
        stocks_info += "【%s】%s 上市日期:%s\n" % (s_info.code, s_info.display_name, s_info.start_date)
    log.info(stocks_info)
