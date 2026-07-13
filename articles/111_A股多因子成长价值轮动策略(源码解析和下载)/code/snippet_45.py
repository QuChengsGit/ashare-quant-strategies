def adjust_position(context, buy_stocks):
    for stock in list(context.portfolio.positions.keys()):
        if stock not in buy_stocks:
            position = context.portfolio.positions[stock]
            close_position(position)

复制
