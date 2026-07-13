def my_trade(context):
    g.count_days += 1
    hold_list0 = []
    position_dict0 = context.subportfolios[0].long_positions
    for position in list(position_dict0.values()):
        hold_list0.append(position.security)
    hold_list1 = []
    position_dict1 = context.subportfolios[1].long_positions
    for position in list(position_dict1.values()):
        hold_list1.append(position.security)
    if g.count_days % 120 == 1:
        if len(hold_list0) != 0:
            for stock in hold_list0:
                order_target_value(stock, 0, pindex=0)
        elif len(hold_list1) != 0:
            for stock in hold_list1:
                order_target_value(stock, 0, pindex=1)
        else:
            print('账户再平衡前没有持仓')
        g.initial_cash = context.portfolio.available_cash / 2
        cash0 = context.subportfolios[0].available_cash
        cash1 = context.subportfolios[1].available_cash
        to_transfer_cash = (max(cash0, cash1) - min(cash0, cash1)) / 2
        if cash0 > cash1:
            transfer_cash(from_pindex=0, to_pindex=1, cash=to_transfer_cash)
        else:
            transfer_cash(from_pindex=1, to_pindex=0, cash=to_transfer_cash)
    target_cash = g.p * g.initial_cash
    if g.count_days % 3 == 1:
        if len(hold_list1) != 0:
            order_target_value(hold_list1[0], 0, pindex=1)
        else:
            print('账户2无持仓')
        if g.buy_stock != 0:
            cash0 = context.subportfolios[0].available_cash
            if cash0 >= target_cash:
                order_target_value(g.buy_stock, target_cash, pindex=0)
            else:
                order_target_value(g.buy_stock, cash0, pindex=0)
        else:
            print('未选出股票')
    elif g.count_days % 3 == 2:
        if g.buy_stock != 0:
 cash1 = context.subportfolios[1].available_cash
            if cash1 >= target_cash:
                order_target_value(g.buy_stock, target_cash, pindex=1)
            else:
                order_target_value(g.buy_stock, cash1, pindex=1)
        else:
            print('未选出股票')
    elif g.count_days % 3 == 0:
        if len(hold_list0) != 0:
            order_target_value(hold_list0[0], 0, pindex=0)
        else:
            print('账户1无持仓')
        if g.buy_stock != 0:
            cash0 = context.subportfolios[0].available_cash
            if cash0 >= target_cash:
                order_target_value(g.buy_stock, target_cash, pindex=0)
            else:
                order_target_value(g.buy_stock, cash0, pindex=0)
        else:
            print('未选出股票')
