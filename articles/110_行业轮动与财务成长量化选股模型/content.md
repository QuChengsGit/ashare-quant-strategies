# 110、行业轮动与财务成长量化选股模型

本策略的核心目标是通过**行业宽度** 、**市场表现** 和**财务指标** 来筛选出具有潜力的股票进行投资，同时采用**动态调整和仓位管理** 来增强投资组合的表现。通过多维度筛选出表现良好的股票，策略基于**行业宽度（即行业内部股票的表现）** 和**个股的财务指标** 进行筛选。策略的一个重要特点是防御性选股，当市场状况不佳时，策略会优先选择具有稳健财务的低估值股票。此外，通过周调整、日常复查涨停股票、过滤异常股票等方式优化组合。**本文完整代码下载地址请见文末。**

  * **行业宽度筛选** ：根据行业中股票的表现来判断哪些行业有潜力。通过判断行业内股票价格是否高于20日均线，筛选出表现最强的行业。

  * **财务筛选** ：结合PE、PB等财务指标，选出具有良好盈利能力和稳健财务的股票。

  * **动态调整持仓** ：每周对持仓进行调整，卖出不符合条件的股票，买入新的优质股票。

  * **防御性策略** ：在市场不确定时，转向低估值、高盈利的防御性股票。

**策略的设计旨在利用市场的趋势和行业表现进行投资，以实现长期稳健的回报** 。下面是对每个功能模块的详细解释，包括其优化思路和设计背后的逻辑。

### 1. **初始化函数 (initialize)**

```python
def initialize(context):
    """
    初始化策略参数和设置
    """
    set_benchmark('000985.XSHG')  # 设置基准指数，常见的做法是选择沪深300等代表性的指数
    set_option('use_real_price', True)  # 使用真实价格进行交易计算
    set_option("avoid_future_data", True)  # 开启防未来函数模式，防止未来数据泄漏
    set_slippage(FixedSlippage(0))  # 设置滑点为0，表示不考虑滑点
    set_order_cost(OrderCost(open_tax=0,
                             close_tax=0.001,
                             open_commission=0.0003,
                             close_commission=0.0003,
                             close_today_commission=0,
                             min_commission=5),
                   type='stock')  # 设置交易成本，包括印花税、佣金等
    log.set_level('order', 'error')  # 设置日志输出级别为'error'，只记录严重问题
    # 初始化全局变量
    g.stock_num = 5  # 计划持有的股票数量
    g.max_hold_stocknum = 1  # 最大持有股票数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 记录昨日涨停的股票列表
    g.num = 1  # 每次选取的行业数量
    # 设置每日和每周定时运行的任务
    run_daily(prepare_stock_list, '9:05')  # 每天9:05运行选股函数，准备股票列表
    run_weekly(weekly_adjustment, 1, '9:30')  # 每周一9:30进行持仓调整
    run_daily(check_limit_up, '14:00')  # 每天14:00检查持仓中的涨停股票是否需要卖出
```

  * **set_benchmark('000985.XSHG')** ：设置沪深300指数（或其它指数）为策略的基准，便于评估策略的表现。

  * **set_option('use_real_price', True)** ：在实际交易时使用实时价格，而非历史价格，以提高策略的真实反应度。

  * **set_option("avoid_future_data", True)** ：防止策略在回测时使用未来数据，确保策略的真实性和科学性。

  * **set_slippage(FixedSlippage(0))** ：假设滑点为0，即没有任何买卖价格偏差，实际操作中可以根据市场情况调整。

  * **set_order_cost(...)** ：设置交易的各项费用，包括佣金和印花税。实际交易中这些因素会影响策略的利润，因此需要精确设置。

  * **run_daily(...) 和 run_weekly(...)** ：定时执行任务，确保策略在每天和每周固定的时间运行选股和调整任务。

### 2. **准备股票列表 (prepare_stock_list)**

```python
def prepare_stock_list(context):
    """
    准备股票列表，获取当前持仓和昨日涨停股票
    """
    g.hold_list = [position.security for position in context.portfolio.positions.values()]  # 获取当前持仓列表
    if g.hold_list:
        # 获取昨日涨停股票
        df = get_price(g.hold_list,
                       end_date=context.previous_date,
                       frequency='daily',
                       fields=['close', 'high_limit'],
                       count=1,
                       panel=False,
                       fill_paused=False)
        df = df[df['close'] == df['high_limit']]  # 筛选出涨停的股票
        g.yesterday_HL_list = list(df.code)
    else:
        g.yesterday_HL_list = []
```

  * **g.hold_list** ：获取当前持仓股票列表，便于在后续处理中排除已经持有的股票。

  * **get_price()** ：获取持仓股票的昨日收盘价和涨停价。利用这些数据来判断是否需要卖出涨停股票。只有在涨停的股票才会加入 g.yesterday_HL_list。

  * **df[df['close'] == df['high_limit']]** ：筛选出昨日涨停的股票，如果持仓中的股票符合这个条件，则加入 g.yesterday_HL_list。

### 3. **行业筛选函数 (industry)**

```python
def industry(stockList, industry_codes, date):
    """
    计算各行业的股票数量
    """
    i_Constituent_Stocks = {}
    for code in industry_codes:
        temp = get_industry_stocks(code, date)  # 获取行业成分股
        i_Constituent_Stocks = list(set(temp).intersection(set(stockList)))  # 计算股票列表和行业成分股的交集
    # 返回各行业的股票数量
    count_dict = {name: len(content_list) for name, content_list in i_Constituent_Stocks.items()}
    return count_dict
```

  * **get_industry_stocks(code, date)** ：从指定行业的代码列表中获取该行业的成分股。

  * **set(temp).intersection(set(stockList))** ：获取股票池与行业成分股的交集，确保我们只关注在目标股票池内的股票。

  * **count_dict** ：计算每个行业中符合条件的股票数量，作为后续决策的依据。

### 4. **选股模块 (get_stock_list)**

```python
def get_stock_list(context):
    """
    选股模块：基于行业宽度和财务指标筛选股票
    """
    yesterday = context.previous_date
    today = context.current_dt
    # 获取中证全指成分股作为初始股票池
    initial_list = get_index_stocks('000985.XSHG', today)
    # 获取股票价格数据并计算20日均线
    h = get_price(initial_list,
                 end_date=yesterday,
                 frequency='1d',
                 fields=['close'],
                 count=21,
                 panel=False)
    df_close = h.pivot(index='code', columns='date', values='close').dropna(axis=0)
    df_ma20 = df_close.rolling(window=20, axis=1).mean().iloc[:, -1:]
    # 判断收盘价是否高于20日均线
    df_bias = (df_close.iloc[:, -1:] > df_ma20)
    # 获取股票行业分类
    s_stk_2_ind = getStockIndustry(p_stocks=initial_list, p_industries_type='sw_l1', p_day=yesterday)
    df_bias['industry_code'] = s_stk_2_ind
    # 计算各行业价格高于均线的股票比例
    df_ratio = (df_bias.groupby('industry_code').sum() * 100.0 / df_bias.groupby('industry_code').count()).round()
    # 选择表现最好的行业
    top_industries = df_ratio.iloc[:, -1].nlargest(g.num).index.tolist()
    # 过滤行业，并使用财务指标进行进一步筛选
    all_stocks = get_all_securities('stock', today).index.tolist()
    sz_stocks = [stock for stock in all_stocks if stock.startswith('002')]  # 选择深市股票
    # 使用财务筛选进一步筛选
    q = query(valuation.code).filter(valuation.code.in_(sz_stocks), valuation.pb_ratio > 0)
    final_list = get_fundamentals(q).set_index('code').index.tolist()
    return final_list
```

  * **get_index_stocks('000985.XSHG', today)** ：获取中证全指（或其它指数）的成分股作为初步筛选的股票池。

  * **计算20日均线 (df_ma20)** ：通过计算每只股票的20日均线并判断股票收盘价是否高于均线，筛选出具有上升趋势的股票。

  * **getStockIndustry(...)** ：将股票与行业代码关联，通过该关联来判断哪些股票属于指定行业。

  * **df_bias.groupby('industry_code').sum() * 100.0 / df_bias.groupby('industry_code').count()** ：计算每个行业内，收盘价高于20日均线的股票占比，作为行业表现的衡量标准。

### 5. **每周调整持仓 (weekly_adjustment)**

```python
def weekly_adjustment(context):
    """
    每周调整持仓：卖出不在目标列表的股票，买入新的股票
    """
    target_stocks = get_stock_list(context)  # 获取目标股票列表
    # 卖出不在目标列表且不是昨日涨停的股票
    for stock in g.hold_list:
        if stock not in target_stocks and stock not in g.yesterday_HL_list:
            position = context.portfolio.positions[stock]
            close_position(position)
    # 计算并买入新的股票
    position_count = len(context.portfolio.positions)
    target_num = len(target_stocks)
    buy_num = min(target_num - position_count, g.stock_num)
    value = context.portfolio.cash / buy_num
    for stock in target_stocks:
        if stock not in context.portfolio.positions:
            if open_position(stock, value):
                if len(context.portfolio.positions) == target_num:
                    break
```

  * **get_stock_list(context)** ：获取当前符合条件的股票列表。

  * **卖出不符合条件的股票** ：遍历当前持仓中的股票，如果该股票不在目标股票池中，并且不是昨日涨停的股票，则进行卖出操作。

  * **open_position(stock, value)** ：买入新的股票，使用可用资金进行均匀分配。

### 6. **检查涨停 (check_limit_up)**

```python
def check_limit_up(context):
    """
    检查持仓中的涨停股票是否需要卖出
    """
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=context.current_dt, frequency='1m', fields=['close', 'high_limit'])
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:  # 如果不涨停则卖出
                log.info("[%s]涨停打开，卖出" % stock)
                position = context.portfolio.positions[stock]
                close_position(position)
```

  * **check_limit_up** ：在每日交易结束前检查持仓中的涨停股票，如果涨停被打开，则卖出该股票，避免可能的风险。

### 总结

这份策略通过结合**行业宽度** 、**财务数据** 和**技术指标** （如20日均线），进行精准的股票筛选和投资组合管理。每周调整持仓，避免盲目持有表现不佳的股票。同时，特别注意涨停股票的风险，实时进行卖出操作，保持仓位的灵活性与安全性。通过这些模块的设计，策略不仅能够利用行业趋势进行选股，还能通过财务数据和技术指标的双重验证，提高投资决策的准确性。

**通过网盘分享的文件：行业轮动与财务成长量化选股模型.zip**

**链接: https://pan.baidu.com/s/1I35ZeGbW_O5GCNbX2CDrUQ 提取码: s3g1**

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
