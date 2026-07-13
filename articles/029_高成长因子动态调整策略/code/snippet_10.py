def market_opened(context):
    if g.is_empty_position == False:
        adjustment(context, context.previous_date)
