def market_opened(context):
    """
    每周一开盘后触发的调仓入口
    """
    yesterday = context.previous_date      # 上一个交易日日期
    # 若不在空仓期，则执行调仓逻辑
    if not g.is_empty_position:
        adjustment(context, yesterday)
