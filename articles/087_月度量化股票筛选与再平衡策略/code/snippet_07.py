def set_default_params(context):
    g.security = '000300.XSHG'  # 基准为沪深300指数
    g.quantile = (0, 10)  # 选择评分前10%的股票
    g.if_trade = False  # 标记是否交易
    set_option('use_real_price', True)
    set_slippage(FixedSlippage(0))

复制
