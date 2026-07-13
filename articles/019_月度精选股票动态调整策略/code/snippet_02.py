def before_trading_start(context):
    prepare_stock_list(context) # 准备股票池
    print(context.run_params.type) # 输出模拟交易参数
