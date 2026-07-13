all_stocks = list(get_all_securities(types=['stock'], date=yesterday).index)
candidate_list = basic_filters(context, all_stocks)


get_all_securities 获取到昨天为止仍有效的全部股票代码。
