# 54、多因子动态选股策略

### 策略介绍：

**多因子动态选股策略** 是一种结合了多种技术指标和基本面筛选的股票投资策略。该策略每周基于行业分析、市场动量、板块强弱等多个因子动态调整股票池，并通过日内实时跟踪市场走势，执行多次买卖操作以实现最佳持仓调整。策略核心在于使用DMI指标（趋向指标）寻找强势股，同时过滤出具备潜在上升空间且波动较小的股票，以实现稳健的投资收益。

### 核心代码及技术文档说明

1\. 初始化函数

```python
from jqdata import *
def initialize(context):
    set_benchmark('000300.XSHG')  # 设置基准指数为沪深300
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 避免使用未来数据进行回测
    log.info('初始函数开始运行且全局只运行一次')
    g.stock_num = 3  # 每次持有的最大股票数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票
    g.candidate_list = []  # 候选股票列表
    g.buy1_stock_lists = []  # 早上待买入的股票列表
    g.buy2_stock_lists = []  # 中午待买入的股票列表
    # 设定交易成本
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 每周一早上运行股票池准备
    run_weekly(weekly_prepare_stock, 1, time='7:00', reference_security='000300.XSHG')
    # 每日开盘时准备当日的股票池
    run_daily(prepare_stock_list, time='9:30', reference_security='000300.XSHG')
    # 开盘时及午盘时卖出不符合条件的股票
    run_daily(my_trade_sell, time='9:30', reference_security='000300.XSHG')
    run_daily(my_trade_sell, time='13:30', reference_security='000300.XSHG')
    # 午盘时检查并卖出昨日涨停但未继续涨停的股票
    run_daily(check_limit_up, time='13:30', reference_security='000300.XSHG')
    # 午盘时买入符合条件的股票
    run_daily(my_trade_buy2, time='13:31', reference_security='000300.XSHG')
    # 收盘后记录交易信息
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
```

技术说明：

  * **基准设置** ：沪深300作为基准指数，用于评估策略表现。

  * **实时价格使用** ：开启真实价格模式，确保交易执行的准确性。

  * **全局变量初始化** ：设置全局变量用于保存持仓、候选股票等信息，并设置每日和每周的交易逻辑。

  * **交易成本设定** ：设定合理的交易成本，模拟真实市场中的手续费和税费。

2\. 股票池准备与筛选函数

```python
# 每周准备股票池
def weekly_prepare_stock(context):
    candidate_list = []
    yes_day = context.previous_date
    df = get_industries(name='sw_l2', date=yes_day)  # 获取申万二级行业的股票分类
    df['score'] = -100000
    df['nums'] = 0
    drop_index = []
    for industry_index in df.index:
        check_out_lists = get_industry_stocks(industry_index, yes_day)
        df.loc[industry_index, 'nums'] = len(check_out_lists)
        if len(check_out_lists) >= 20:
            score = stock_sector_score(check_out_lists, 10)  # 计算行业得分
            df.loc[industry_index, 'score'] = score
        else:
            drop_index.append(industry_index)
    df = df.drop(drop_index).sort_values(by=['score'], ascending=False)
    industry_indexs = df.index[:5]  # 选择得分最高的5个行业
    for industry_index in industry_indexs:
        if df.loc[industry_index, 'score'] > 500:
            check_out_lists = get_industry_stocks(industry_index, yes_day)
            candidate_list.extend(check_out_lists)
    candidate_list = list(set(candidate_list))
    candidate_list = filter_new_stock(context, candidate_list)
    candidate_list = filter_kcbj_stock(candidate_list)
    candidate_list = filter_st_stock(candidate_list)
    candidate_list = filter_paused_stock(candidate_list)
    candidate_list = find_strong_stock(context, candidate_list)
    g.candidate_list = candidate_list[:min(g.stock_num + 10, len(candidate_list))]
    log.info("一周准备的股票LIST %0d,如下:" % len(g.candidate_list))
    log.info(g.candidate_list)
# 每日准备股票池
def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.yesterday_HL_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.yesterday_HL_list = []
    g.buy1_stock_lists = []
    g.buy2_stock_lists = []
    candidate_list = find_strong_stock(context, g.candidate_list)
    candidate_list = candidate_list[:min(g.stock_num * 2, len(candidate_list))]
    for stock in candidate_list:
        dt = attribute_history(stock, 1, '1d', ['close', 'pre_close', 'open'])
        if (dt.close[-1] > dt.pre_close[-1] * 1.01 and dt.close[-1] > dt.open[-1] and
                context.current_data[stock].day_open < dt.close[-1] * 0.97):
            g.buy1_stock_lists.append(stock)
        else:
            g.buy2_stock_lists.append(stock)
    log.info("早上待买入的股票:", g.buy1_stock_lists)
    log.info("中午待买入的股票:", g.buy2_stock_lists)
```

技术说明：

  * **股票池准备** ：每周筛选出得分最高的行业，并选出其中的强势股作为候选股票池。每日更新持仓信息，准备当日可以交易的股票列表。

  * **行业得分计算** ：根据行业中股票的整体表现打分，得分较高的行业可能具有较高的潜在收益。

  * **强势股筛选** ：使用DMI指标选出技术面表现较好的强势股，以提高买入成功率。

3\. 买卖交易函数

```python
# 卖出下跌的股票
def my_trade_sell(context):
    sell_stocks = []
    holding_list = list(context.portfolio.positions)
    if holding_list:
        for stock in holding_list:
            dt = attribute_history(stock, 1, '1d', ['close'])
            if context.current_data[stock].last_price <= dt.close[-1] * 0.98:
                sell_stocks.append(stock)
        if sell_stocks:
            send_message("[%s]跌幅过大，卖出" % ' '.join(sell_stocks))
            log.info("[%s]跌幅过大，卖出" % ' '.join(sell_stocks))
            for stock in sell_stocks:
                position = context.portfolio.positions[stock]
                close_position(position)
# 检查昨日涨停股票并卖出未继续涨停的
def check_limit_up(context):
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=context.current_dt, frequency='1m',
                                     fields=['close', 'high_limit'], skip_paused=False, fq='pre',
                                     count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                send_message("[%s]涨停打开，卖出" % stock)
                log.info("[%s]涨停打开，卖出" % stock)
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                send_message("[%s]涨停，继续持有" % stock)
                log.info("[%s]涨停，继续持有" % stock)
# 中午买入符合条件的股票
def my_trade_buy2(context):
    buy_stocks = g.buy2_stock_lists[:]
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            dt = attribute_history(stock, 1, '1d', ['close'])
            if (context.current_data[stock].last_price > dt.close[-1]
 * 1.01 and
                    context.current_data[stock].last_price < context.current_data[stock].high_limit and
                    context.portfolio.positions[stock].total_amount == 0):
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.stock_num:
                        break
```

技术说明：

  * **卖出逻辑** ：卖出当日跌幅超过2%或昨日涨停但未继续涨停的股票，以减少可能的损失。

  * **买入逻辑** ：中午买入符合条件的股票，特别是那些在技术面上表现出强劲趋势的股票。

4\. 辅助函数

```python
# 开仓操作
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
# 平仓操作
def close_position(position):
    order = order_target_value_(position.security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
```

技术说明：

  * **开仓和平仓** ：确保交易操作成功执行，通过判断订单状态和成交量来确认交易是否成功。

### 策略优势：

  * **多因子筛选** ：结合基本面和技术面多个因子筛选股票，提高了选股的准确性和收益潜力。

  * **动态调整** ：每周更新股票池，每日根据市场变化调整持仓，灵活应对市场波动。

  * **风险控制** ：通过卖出跌幅较大的股票和避免风险较高的股票（如ST股票），有效控制投资组合风险。

### 总结：

**多因子动态选股策略** 通过多因子分析和动态选股机制，实现了股票投资的高效管理。该策略适合在波动市场中寻找短期机会，同时通过严格的风险管理措施，力求在市场的不同阶段都能取得良好的表现。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
