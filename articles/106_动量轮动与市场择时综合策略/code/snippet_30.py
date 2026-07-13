def check_lose(context):
    for position in context.portfolio.positions.values():
        if (position.price / position.avg_cost - 1) * 100 <= -15:
            order_target_value(position.security, 0)  # 触发止损

复制
