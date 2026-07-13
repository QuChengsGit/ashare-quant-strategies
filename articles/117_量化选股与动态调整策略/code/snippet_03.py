def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = list(set(get_all_securities().index) & set(get_hot_industry_stock(context)))
    initial_list = filter_new_stock(context, initial_list)  # 过滤新股
    initial_list = filter_kcb_stock(context, initial_list)  # 过滤科创板股票
    initial_list = filter_st_stock(initial_list)  # 过滤ST股
    ...
    final_list = [sg_list, ms_list, peg_list]
    return final_list
