# 卖出下跌的股票
def my_trade_sell(context):
    sell_stocks = []
    holding_list = list(context.portfolio.positions)
    if holding_list:
        for stock in holding_list:
            dt = attribute_history(stock, 1, '1d', ['close'])
            if context.current_data[stock].last_price <= dt.close[-1] * 0.98:
                sell_stocks.append(stock)
        if sell_stocks:
            send_message("[%s]跌幅过大，卖出" % ' '.join(sell_stocks))
            log.info("[%s]跌幅过大，卖出" % ' '.join(sell_stocks))
            for stock in sell_stocks:
                position = context.portfolio.positions[stock]
                close_position(position)
# 检查昨日涨停股票并卖出未继续涨停的
def check_limit_up(context):
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=context.current_dt, frequency='1m',
                                     fields=['close', 'high_limit'], skip_paused=False, fq='pre',
                                     count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                send_message("[%s]涨停打开，卖出" % stock)
                log.info("[%s]涨停打开，卖出" % stock)
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                send_message("[%s]涨停，继续持有" % stock)
                log.info("[%s]涨停，继续持有" % stock)
# 中午买入符合条件的股票
def my_trade_buy2(context):
    buy_stocks = g.buy2_stock_lists[:]
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            dt = attribute_history(stock, 1, '1d', ['close'])
            if (context.current_data[stock].last_price > dt.close[-1]
 * 1.01 and
                    context.current_data[stock].last_price < context.current_data[stock].high_limit and
                    context.portfolio.positions[stock].total_amount == 0):
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        break

复制
