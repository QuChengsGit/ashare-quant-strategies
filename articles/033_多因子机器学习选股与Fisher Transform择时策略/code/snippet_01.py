def initialize(context):
    set_params()
    set_backtest()
    g.factors = ['alpha_006', 'alpha_015', 'alpha_026']  # 选取的alpha因子
