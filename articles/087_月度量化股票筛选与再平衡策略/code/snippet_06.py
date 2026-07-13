def initialize(context):
    # 设定上证指数作为基准
    set_default_params(context)  # 初始化系统参数
    set_benchmark(g.security)  # 设置基准为沪深300指数
    # 加载评分数据
    g.df_dic = {}
    tmp_df_dic = pickle.loads(read_file('test_predict_300_q.pkl'))
    for dd, df in tmp_df_dic.items():
        if len(df) == 0:
            continue
        g.df_dic[dd.rsplit('-', 1)[0]] = df.sort_values(by='score', ascending=False)
    run_daily(before_market_open, time='before_open')
    run_daily(market_open, time='open', reference_security=g.security)

复制
