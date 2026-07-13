def initialize(context):
    g.mode = 0
    g.record = 0.0
    g.times = -1
    g.order_amount = 0.04
    g.begin_date = '2013-01'
    g.stock_security = '510300.XSHG'
    g.bond_security = '511010.XSHG'
    g.over_hot = False
    g.yearMa10 = 0.0
    set_benchmark('000300.XSHG')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    run_daily(handle, time='14:55')
