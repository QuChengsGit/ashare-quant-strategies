# 53、市值加权股票精选策略

### 策略介绍：

**市值加权股票精选策略** 是一种基于市值排序的量化选股策略，旨在从市场中筛选出市值最低的股票进行投资。该策略通过剔除特定类型的股票（如科创板、北交所股票，以及ST、*ST和具有退市风险的股票），确保投资组合的稳定性和流动性。然后，策略按市值排序，选择市值最小的400只股票进行均值加权投资。该策略旨在捕捉市值较小公司的潜在高增长性，同时分散投资以降低个股风险。

### 核心代码及技术文档说明

1\. 初始化函数

```python
from jqdata import *
def initialize(context):
    set_benchmark('399303.XSHE')  # 设置基准指数为创业板综指
    set_option('use_real_price', True)  # 使用真实价格
    set_option("avoid_future_data", True)  # 避免使用未来数据进行回测
    log.set_level('system', 'error')  # 设置日志级别为错误，减少冗余输出
    g.stock_num = 400  # 设置选股数量
    run_daily(rebalance, '9:30')  # 每日9:30进行调仓
```

技术说明：

  * **基准设置** ：将创业板综指（399303.XSHE）作为基准，以便与策略表现进行对比。

  * **实时价格使用** ：策略使用真实价格进行交易，确保交易的准确性。

  * **回测设置** ：避免使用未来数据，确保策略回测的严谨性和可靠性。

  * **选股数量** ：设定每次调仓时最多持有400只股票，以控制投资组合的分散度。

2\. 调仓函数

```python
def rebalance(context):
    stocks = get_all_securities('stock').index.tolist()  # 获取所有股票列表
    stocks = filter_kcbj_stock(stocks)  # 过滤科创板和北交所股票
    stocks = filter_st_stock(stocks)  # 过滤ST及退市风险股票
    # 按市值升序选取市值最小的股票
    df = get_fundamentals(query(valuation.code, valuation.market_cap)
        .filter(valuation.code.in_(stocks))
        .order_by(valuation.market_cap.asc())
        .limit(g.stock_num))
    selected_stocks = list(df.code)  # 获取最终选中的股票代码
    # 卖出不再持有的股票
    for s in context.portfolio.positions:
        if s not in selected_stocks:
            order_target_value(s, 0)
    # 计算每只股票的目标持仓市值
    value_per_stock = context.portfolio.total_value / g.stock_num
    balance = {}
    for s in selected_stocks:
        if s in context.portfolio.positions:
            diff = value_per_stock - context.portfolio.positions[s].value
        else:
            diff = value_per_stock
        balance[s] = diff
    # 按需调整每只股票的持仓
    for s in dict(sorted(balance.items(), key=lambda x: x[1], reverse=False)).keys():
        order_target_value(s, value_per_stock)
    # 记录总市值变化
    total_market_cap = df.market_cap.sum()
    record(market_cap=total_market_cap)
```

技术说明：

  * **股票筛选** ：通过剔除科创板、北交所股票和ST股票，保证投资组合的质量和稳定性。

  * **市值排序** ：按市值升序排序，选择市值最小的股票，以期望捕捉高成长潜力。

  * **持仓调整** ：计算每只股票的目标持仓市值，并按差异调整持仓，以达到均值加权分配。

  * **调仓逻辑** ：通过每日9:30运行调仓函数，动态调整组合，及时响应市场变化。

3\. 股票筛选辅助函数

```python
# 过滤科创板和北交所股票
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock.startswith('4') or stock.startswith('8') or stock.startswith('68'))]
# 过滤ST及退市风险股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st
            and 'ST' not in current_data[stock].name
            and '*' not in current_data[stock].name
            and '退' not in current_data[stock].name]
```

技术说明：

  * **科创板和北交所股票过滤** ：通过筛选代码前缀的方式，剔除科创板和北交所的股票，降低交易风险。

  * **ST股票过滤** ：过滤掉ST、*ST及其他具有退市风险的股票，确保投资组合的稳定性。

### 策略优势：

  * **小市值优势** ：策略通过选择市值较小的股票，有可能捕捉到高成长潜力的股票，从而提高收益率。

  * **风险控制** ：通过剔除特定高风险股票（如ST股票），降低了组合的风险暴露。

  * **均值加权** ：通过将投资分散在多只股票上，降低了个股波动对组合的影响，提升了策略的稳定性。

### 总结：

**市值加权股票精选策略** 通过市值排序和严格的股票筛选机制，构建了一个具有高成长潜力的投资组合。策略结合了市值最小化和风险控制的优势，在保证投资组合质量的同时，力求实现更高的风险调整收益。该策略适合在市场中寻找成长机会的投资者，同时通过分散投资降低风险。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
