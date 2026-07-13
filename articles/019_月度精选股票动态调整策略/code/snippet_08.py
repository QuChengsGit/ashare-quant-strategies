def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] in ['4', '8'] or stock[:2] == '68')]
