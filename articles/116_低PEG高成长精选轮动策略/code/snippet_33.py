all_stocks = list(get_all_securities(types=['stock'], date=yesterday).index)
candidate_list = basic_filters(context, all_stocks)

复制
