def market_open_sell_buy(context):
    inntraday_trading(context)
    clearn_every_bar(context)
    g.run_count+=1
    if g.run_count==240: 
        g.run_count=0
def clearn_every_bar(context):
    curr_data=get_current_data()
    hour=context.current_dt.hour
    minute=context.current_dt.minute
    sells=list(context.portfolio.positions)
    for s in sells: 
        if context.portfolio.positions[s].closeable_amount<=0:
            continue
        dfmcount = attribute_history(s,(g.run_count+1),'1m',['close'],skip_paused=True)
        if dfmcount.close[-1]
