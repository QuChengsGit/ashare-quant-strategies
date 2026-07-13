def pre_hold_check(context):
    if context.portfolio.positions:
        for stk in context.portfolio.positions:
            dt = attribute_history(stk, g.lossN + 2, '60m', ['close'])
            dt['man'] = dt.close / dt.close.rolling(g.lossN).mean()
            if dt.man[-1] < 1.0:
                log.info("盘中可能止损，卖出：{}".format(stk))
                send_message("盘中可能止损，卖出：{}".format(stk))
def hold_check(context):
    current_data = get_current_data()
    if context.portfolio.positions:
        for stk in context.portfolio.positions:
            yesterday_di = attribute_history(stk, 1, '1d', ['close'])
            dt = attribute_history(stk, g.lossN + 2, '60m', ['close'])
            dt['man'] = dt.close / dt.close.rolling(g.lossN).mean()
            if dt.man[-1] < 1.0 and current_data[stk].last_price * g.lossFactor <= yesterday_di['close'][-1]:
                stk_dict = context.portfolio.positions[stk]
                log.info('准备平仓，总仓位:{}, 可卖出：{}, '.format(stk_dict.total_amount, stk_dict.closeable_amount))
                send_message("盘中止损，卖出：{}".format(stk))
                if stk_dict.closeable_amount:
                    order_target_value(stk, 0)
                    log.info('盘中止损', stk)
                else:
                    log.info('无法止损', stk)
