def get_stock_list(context):
    yesterday = context.previous_date
    today = context.current_dt
    initial_list = get_all_securities('stock', today).index.tolist()
    initial_list = filter_all_stock2(context, initial_list)
    tensor_list = []
    for i in initial_list:
        df = attribute_history(i, 60, '1d')
        df_tensor = torch.Tensor(df.values)
        tensor_list.append(df_tensor)
    stacked_tensor = torch.stack(tensor_list)
    with torch.no_grad():
        output1 = model_t1(stacked_tensor)
        output2 = model_t2(stacked_tensor)
        output3 = model_t3(stacked_tensor)
        output = output1 + output2 + output3
        output = output[:, 1]
    data = {'ID': initial_list, 'score': output.squeeze().tolist()}
    df = pd.DataFrame(data)
    top_N_rows = df.nlargest(g.stock_num, 'score')
    top_N_IDs = top_N_rows['ID'].tolist()
    return top_N_IDs
def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        for stock in g.hold_list:
            if stock not in target_list and stock not in g.yesterday_HL_list:
                position = context.portfolio.positions[stock]
                close_position(position)
        position_count = len(context.portfolio.positions)
        target_num = len(target_list)
        if target_num > position_count:
            value = context.portfolio.cash / (target_num - position_count)
            for stock in target_list:
                if context.portfolio.positions[stock].total_amount == 0:
                    if open_position(stock, value):
                        if len(context.portfolio.positions) == target_num:
                            break

复制
