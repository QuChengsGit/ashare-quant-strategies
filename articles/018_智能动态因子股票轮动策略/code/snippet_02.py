import pandas as pd
def initialize(context):
    """
    初始化策略设置
    """
    log.set_level('order', 'error')  # 设置日志级别为错误
    set_option('use_real_price', True)  # 使用真实价格
    set_option('avoid_future_data', True)  # 避免使用未来数据
    g.days = 0  # 初始化运行天数
def after_code_changed(context):
    """
    更新策略配置，当代码更改时调用
    """
    unschedule_all()  # 取消所有已计划的事件
    run_daily(iUpdate, time='before_open')  # 每天开盘前更新股票池
    run_daily(iTrader, time='9:35')  # 每天9:35进行交易操作
    run_daily(iReport, time='after_close')  # 每天收盘后生成报告
def iUpdate(context):
    """
    更新股票池和持仓
    """
    nchoice = 120  # 股票池选择数量
    nposition = 100  # 最大持仓数量
    dt_last = context.previous_date  # 上一个交易日
    all_stock = get_all_securities('stock', dt_last)  # 获取所有股票
    cdata = get_current_data()  # 获取当前数据
    stocks = [s for s in all_stock.index if not cdata[s].is_st]  # 过滤ST股
    # 筛选市场资本小的股票，并按市场资本升序排序
    df = get_fundamentals(
        query(
            valuation.code,
            valuation.market_cap,
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,
        ).order_by(valuation.market_cap.asc()).limit(nchoice)
    ).dropna().set_index('code')
    g.choice = df.index.tolist()  # 更新选股列表
    g.position_size = 1.0 / nposition * context.portfolio.total_value  # 计算每个股票的持仓大小
def iTrader(context):
    """
    执行交易操作
    """
    choice = g.choice  # 获取选股列表
    position_size = g.position_size  # 每个股票的持仓大小
    lm_value = 0.8 * position_size  # 低于此值的持仓需要增加
    hm_value = 1.2 * position_size  # 高于此值的持仓需要减少
    cdata = get_current_data()  # 获取当前数据
    # 卖出操作
    for s in context.portfolio.positions:
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue  # 过滤停牌或价格异常的股票
        if s not in choice:
            log.info('sell', s, cdata[s].name)
            order_target(s, 0, MarketOrderStyle(0.99 * cdata[s].last_price))  # 卖出不在股票池中的股票
    # 买入操作
    for s in choice:
        if context.portfolio.available_cash < position_size:
            break  # 现金不足，停止买入
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue  # 过滤停牌或价格异常的股票
        if s not in context.portfolio.positions:
            log.info('buy', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01 * cdata[s].last_price))  # 买入不在持仓中的股票
        elif context.portfolio.positions[s].value < lm_value:
            log.info('balance+', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01 * cdata[s].last_price))  # 增加低于阈值的持仓
        elif context.portfolio.positions[s].value > hm_value:
            log.info('balance-', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(0.99 * cdata[s].last_price))  # 减少高于阈值的持仓
def iReport(context):
    """
    每日生成报告
    """
    g.days += 1  # 更新运行天数
    log.info('  positions', len(context.portfolio.positions))  # 打印当前持仓数量
    log.info('  return %.2f', 100 * context.portfolio.returns)  # 打印投资回报率
    log.info('  cash %.2f', context.portfolio.available_cash / 10000)  # 打印可用现金
    log.info('  value %.2f', context.portfolio.total_value / 10000)  # 打印投资组合总价值
    log.info('running days', g.days)  # 打印运行天数

复制
