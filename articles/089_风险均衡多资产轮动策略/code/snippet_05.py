def fun_record(self, context, stock):
    tmpDict = g.transactionRecord.copy()
    myPrice = context.portfolio.positions[stock].price
    newAmount = context.portfolio.positions[stock].total_amount
    myAmount = tmpDict[stock]['amount']
    myAvg_cost = tmpDict[stock]['avg_cost']
    if myAmount != newAmount:
        if myAmount <= newAmount:
            myAvg_cost = ((myAvg_cost * myAmount) + myPrice * (newAmount - myAmount)) / newAmount
            tmpDict[stock]['buy_times'] += 1
        elif newAmount == 0:
            myMargin = (myPrice - myAvg_cost) * myAmount
            if myMargin < 0:
                if myMargin <= tmpDict[stock]['max_loss']:
                    tmpDict[stock]['max_loss'] = float(round(myMargin, 2))
                    tmpDict[stock]['max_loss_date'] = context.current_dt
            tmpDict[stock]['Margin'] += float(round(myMargin, 2))
            tmpDict[stock]['sell_times'] += 1
        elif myAmount > newAmount:
            myAvg_cost = ((myAvg_cost * myAmount) - (myPrice * (myAmount - newAmount))) / newAmount
            tmpDict[stock]['sell_times'] += 1
    tmpDict[stock]['amount'] = float(newAmount)
    tmpDict[stock]['avg_cost'] = float(myAvg_cost)
    g.transactionRecord = tmpDict.copy()
def fun_print_transactionRecord(self, context):
    tmpDict = g.transactionRecord.copy()
    message = "\n" + "stock, Win, loss, buy_times, sell_times, Margin, max_loss, max_loss_date, avg_cost\n"
    for stock in tmpDict.keys():
        message += stock + ", "
        message += str(tmpDict[stock]['win']) + ", " + str(tmpDict[stock]['loss']) + " , "
        message += str(tmpDict[stock]['buy_times']) + ", " + str(tmpDict[stock]['sell_times']) + ", "
        message += str(tmpDict[stock]['Margin']) + ", "
        message += str(tmpDict[stock]['max_loss']) + ", " + str(tmpDict[stock]['max_loss_date']) + ", "
        message += str(tmpDict[stock]['avg_cost']) + "\n"
    message += "Returns = " + str(round(context.portfolio.returns, 5) * 100) + "%\n"
    return message
