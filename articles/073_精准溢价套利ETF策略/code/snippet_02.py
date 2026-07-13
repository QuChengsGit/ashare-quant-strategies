from jqdata import *
import datetime
import talib
from jqlib.technical_analysis import *
import sys
import requests
## 初始化函数，设定基准等
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.00025, 
                             close_commission=0.00025, close_today_commission=0, min_commission=5), 
                   type='fund')
    log.set_level('order', 'error')
    g.least_premium = 2.5
    g.least_money = 1.0e7
    g.trade_fee_ratio = 0.00025
    g.ETFNum_hold = 2
    g.etf_df = []
    do_schedule(context)
def after_code_changed(context):
    unschedule_all()
    do_schedule(context)
def do_schedule(context):   
    run_daily(pre_process, '09:15', reference_security='000300.XSHG')
    run_daily(exe_sell, '09:30', reference_security='000300.XSHG')
    run_daily(exe_buy, '09:30', reference_security='000300.XSHG')
def pre_process(context):
    etf_list = get_all_securities(['etf'], context.previous_date).index.tolist()
    df = history(count=1, unit='1d', field="money", security_list=etf_list).T
    df.columns = ['money']
    df = df[df.money > g.least_money]
    today = datetime.datetime.now().date().strftime("%Y-%m-%d")
    current_dt = context.current_dt.strftime("%Y-%m-%d")
    if current_dt < today:
        df = get_extras('unit_net_value', df.index.tolist(), end_date=context.previous_date, df=True, count=1).T
        df.columns = ['unit_net_value']
    else:
        df['unit_net_value'] = [get_etf_value(etf) for etf in df.index.tolist()]
        df = df[df.unit_net_value != -1]
    g.etf_df = df
def exe_sell(context):
    df = g.etf_df
    current = get_current_data()
    df['day_open'] = [current[c].day_open for c in df.index.tolist()]
    df['premium'] = (df.day_open / df.unit_net_value - 1) * 100
    df['factor'] = [attribute_history(c, 1, '1d', fields=['factor'])['factor'][-1] for c in df.index.tolist()]
    df = df[df['factor'] == 1]
    df = df[abs(df['premium']) < 20]
    df = df.sort_values(['premium'], ascending=True)
    df = df[df.premium < -1.0 * g.least_premium]
    order_etf = df[:g.ETFNum_hold].index.tolist()
    etf_to_sell = list(set(context.portfolio.positions.keys()) - set(order_etf))
    for etf in etf_to_sell:
        if context.portfolio.positions[etf].closeable_amount:
            limit_price = current[etf].day_open * 0.98
            order_sell = order_target(etf, 0, LimitOrderStyle(limit_price))
            if order_sell:
                log.info("成功卖出基金 %s【%s】" %  (get_security_info(etf).display_name, etf))
            else:
                log.info("未成功卖出基金 %s【%s】" %  (get_security_info(etf).display_name, etf))
def exe_buy(context):
    least_money_to_buy = 5.00 / g.trade_fee_ratio
    if context.portfolio.available_cash < least_money_to_buy:
        return
    current = get_current_data()
    df = g.etf_df
    df['day_open'] = [current[c].day_open for c in df.index.tolist()]
    df['premium'] = (df.day_open / df.unit_net_value - 1) * 100
    df['factor'] = [attribute_history(c, 1, '1d', fields=['factor'])['factor'][-1] for c in df.index.tolist()]
    df = df[df['factor'] == 1]
    df = df[abs(df['premium']) < 20]
    df = df.sort_values(['premium'], ascending=True)
    df = df[df.premium < -1.0 * g.least_premium]
    order_etf = df[:g.ETFNum_hold].index.tolist()
    to_buy_set = set(order_etf) | set(context.portfolio.positions.keys())
    to_buy_list = list(to_buy_set)
    cash_per_etf = context.portfolio.available_cash / len(to_buy_list)
    if cash_per_etf > least_money_to_buy:
        for etf in to_buy_list:
            limit_price = current[etf].day_open * 1.02
            num_to_buy = int(cash_per_etf / (limit_price * 1.005 * 1.00025) / 100) * 100
            order_buy = order_target(etf, num_to_buy, LimitOrderStyle(limit_price))
            if order_buy:
                log.info("成功买入基金 %s【%s】：%s 股" %  (get_security_info(etf).display_name, etf, order_buy.filled))
            else:
                log.info("未成功买入基金 %s【%s】" %  (get_security_info(etf).display_name, etf))
def after_trading_end(context):
    log.info('交易日结束，感谢参与！')
def get_etf_value(stockcode):
    stockcode = stockcode[:6]
    url = " + stockcode + ".html"
    response = requests.get(url)
    etfDataInfo = response.text
    tmp_str = "fix_dwjz  bold ui-color-green"
    init_position = etfDataInfo.find(tmp_str)
    if init_position == -1:
        return -1
    else:
        init_position += len(tmp_str)
        etf_value = float(etfDataInfo[init_position + 2:init_position + 8])
        return etf_value

复制
