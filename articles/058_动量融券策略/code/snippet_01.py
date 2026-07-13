from jqdata import *
def initialize(context):
    set_benchmark('000300.XSHG')  # 设定基准指数为沪深300
    set_option('use_real_price', True)  # 启用动态复权模式，确保使用真实价格进行交易
    log.info('初始函数开始运行且全局只运行一次')
    # 设置融资融券账户配置
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.cash, type='stock_margin')])
    # 融资融券相关参数设定
    set_option('margincash_interest_rate', 0.08)  # 设定融资利率为年化8%
    set_option('margincash_margin_rate', 1.5)  # 设定融资保证金比率为150%
    set_option('marginsec_interest_rate', 0.10)  # 设定融券利率为年化10%
    set_option('marginsec_margin_rate', 1.5)  # 设定融券保证金比率为150%
    # 设置交易成本与滑点
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    set_slippage(PriceRelatedSlippage(0.00246), type='stock')  # 设置滑点为千分之二点四六
    # 设定运行函数
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(clear_close, time='14:55', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
