from jqdata import *
from jqfactor import *
import pandas as pd
import numpy as np
import time
from six import BytesIO
# 初始化函数，设定基准等等
def initialize(context):
    # 最大持仓数量
    g.max_stock_count = 5
    # 牛熊市场参数设定
    g.MA = ['399008.XSHE', 10]  # 中小300指数和均线周期
    g.threshold = 0.003  # 牛熊切换阈值
    g.isbull = False  # 当前是否为牛市
    g.bearpercent = 0.5  # 熊市股票持仓比例（原值为30%）
    # 交易规则参数
    g.hold_interval = 10  # 最短持仓时间（天）
    g.selldate_interval = 5  # 卖出后再买入间隔时间（天）
    g.top_withdraw_ratio = 0.03  # 最高点回撤比例
    # 债券基金
    g.bond = '511010.XSHG'
    # 交易统计与记录
    g.statistics_df = pd.DataFrame(columns=['code', 'name', 'date_buy', 'price_buy', 'date_sell', 'price_sell', 'ratio', 'result'])
    g.sell_history_df = pd.DataFrame(columns=['code', 'name', 'last_date_sell'])
    # 股票名称缓存
    g.stocks_allnames_df = get_all_securities()
    # 设置基准为沪深300
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    log.info('策略初始化完成')
    log.set_level('order', 'error')
    # 设置股票交易费用
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 定时任务
    run_daily(before_market_open, time='before_open')
    run_daily(market_open, time='14:55')
    run_daily(after_market_close, time='after_close')
## 开盘前运行函数
def before_market_open(context):
    pass
## 开盘时运行函数
def market_open(context):
    date = context.current_dt.strftime("%Y-%m-%d")
    # 判断牛熊趋势
    get_bull_bear_signal_minute()
    # 建仓程序
    buy_df = get_df_fromfile(context)
    buylist = buy_df['code'].tolist()
    if not buylist:
        log.info('当日无建仓信号')
    else:
        log.info('今日建仓列表:' + str(buy_df))
        adjust_position(context, buylist)
## 收盘后运行函数
def after_market_close(context):
    log.info('############################一天结束###############################')
def on_strategy_end(context):
    log.info('策略执行结束，总资产 = ' + str(context.portfolio.total_value))
# 获取当天的买入信号CSV文件，返回待买入股票列表的df
def get_df_fromfile(context):
    date = context.current_dt.strftime("%Y-%m-%d")
    file_name = f'8.Mutifactors/Signal_for_trade_{date}.csv'
    log.info('读取买入信号文件：' + str(file_name))
    return pd.read_csv(BytesIO(read_file(file_name)))
# 调仓函数，输入股票列表，自动完成调仓操作
def adjust_position(context, buylist):
    date = context.current_dt.strftime("%Y-%m-%d")
    total_value = round(context.portfolio.total_value, 2)
    # 牛熊市判断及仓位调整
    if g.isbull:
        log.info('当前牛市，股票满仓')
        mkt_ratio = 1
    else:
        log.info('当前熊市，股债搭配')
        mkt_ratio = g.bearpercent
    positions_value_stock = round(total_value * mkt_ratio, 2)
    positions_value_bond = round(total_value - positions_value_stock, 2)
    # 止盈与清仓
    for stock in context.portfolio.positions.keys():
        avg_cost = context.portfolio.positions[stock].avg_cost
        current_price = context.portfolio.positions[stock].price
        buy_in_date = context.portfolio.positions[stock].init_time.strftime('%Y-%m-%d')
        df_price = get_price(stock, start_date=buy_in_date, end_date=context.previous_date, frequency='daily', fields=['close'])
        max_price = df_price['close'].max()
        final_profit_ratio = (current_price / avg_cost) - 1
        if (stock != g.bond) and ((1 - (current_price / max_price)) > g.top_withdraw_ratio):
            order_target_value(stock, 0)
            log.info(f'个股止盈清仓: {stock} 盈利比例: {round(final_profit_ratio * 100, 2)}%')
            continue
        if (stock != g.bond) and check_hold_interval(context, stock, g.hold_interval):
            order_target_value(stock, 0)
            log.info(f'个股到期清仓: {stock} 盈利比例: {round(final_profit_ratio * 100, 2)}%')
    # 牛熊市转换时的仓位调整
    if (g.isbull == False) and (g.bond not in context.portfolio.positions):
        log.info(f'牛转熊，调整仓位，股票比例: {mkt_ratio * 100}%, 债券比例: {100 - mkt_ratio * 100}%')
        for stock in context.portfolio.positions.keys():
            target_value = context.portfolio.positions[stock].value * g.bearpercent
            order_target_value(stock, target_value)
            log.info(f'减仓个股: {stock}')
        order_target_value(g.bond, positions_value_bond)
        log.info(f'建仓债券: {positions_value_bond}')
    if (g.isbull == True) and (g.bond in context.portfolio.positions):
        log.info(f'熊转牛，调整仓位，股票比例: {mkt_ratio * 100}%, 债券比例: {100 - mkt_ratio * 100}%')
        order_target_value(g.bond, 0)
        log.info('清仓债券')
        for stock in context.portfolio.positions.keys():
            target_value = context.portfolio.positions[stock].value / g.bearpercent
            order_target_value(stock, target_value)
            log.info(f'补仓个股: {stock}')
    # 建仓新股票
    stock_position_count = len(context.portfolio.positions) - (1 if g.bond in context.portfolio.positions else 0)
    if stock_position_count < g.max_stock_count:
        value = context.portfolio.available_cash / (g.max_stock_count - stock_position_count)
        for stock in buylist:
            if (stock not in context.portfolio.positions) and check_selldate_interval(date, stock):
                order_target_value(stock, value)
                log.info(f'新增股票建仓: {stock} 目标仓位: {value}')
                if len(context.portfolio.positions) == g.max_stock_count + (1 if g.bond in context.portfolio.positions else 0):
                    break
    else:
        log.info('仓位已满，无法建仓')
# 检验某只股票距离上次卖出时间是否大于设定天数
def check_selldate_interval(date, code):
    if code in g.sell_history_df.values:
        last_date_sell = g.sell_history_df.loc[g.sell_history_df.code == code].last_date_sell.values[0]
        start = time.mktime(time.strptime(last_date_sell, '%Y-%m-%d'))
        end = time.mktime(time.strptime(date, '%Y-%m-%d'))
        count_days = int((end - start) / (24 * 60 * 60))
        if count_days < g.selldate_interval:
            log.info(f'距离最近卖出时间: {count_days}天，无法再次购买: {code}')
            return False
        log.info(f'距离最近卖出时间: {count_days}天，可以再次购买: {code}')
        return True
    log.info(f'卖出历史中无记录，可以建仓: {code}')
    return True
# 检验某只股票持有时间是否超过设定天数
def check_hold_interval(context, code, hold_interval):
    init_time = context.portfolio.positions[code].init_time
    count_days = (context.current_dt - init_time).days
    if count_days > hold_interval:
        log.info(f'持仓时间为: {count_days}天，可以卖出: {code}')
        return True
    log.info(f'持仓时间仅为: {
