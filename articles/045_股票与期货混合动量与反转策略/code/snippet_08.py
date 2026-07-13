def rebalance(context):
    total_value = context.portfolio.total_value
    expected_stock_value = total_value * g.stock_share
    # 资金划转，确保各子账户资金比例
    transfer_cash(1, 0, min(context.subportfolios[1].transferable_cash, max(0, expected_stock_value-context.subportfolios[0].total_value)))
    transfer_cash(0, 1, min(context.subportfolios[0].transferable_cash, max(0, context.subportfolios[0].total_value-expected_stock_value)))
    stock_value = min(context.subportfolios[0].total_value, expected_stock_value)

复制
