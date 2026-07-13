def set_params():
    g.index_symbol = '000300.XSHG'  # 目标指数
    g.N = 50  # 选择前N名的股票
    g.method = 'not_timing'  # 可选方法：'SVM', 'Logistic', 'RandomForest', 'not_timing'
    g.stocks_df = pd.DataFrame()

复制
