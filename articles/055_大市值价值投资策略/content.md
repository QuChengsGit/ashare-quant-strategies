# 55、大市值价值投资策略

### 策略介绍：

**大市值价值投资策略** 是一种基于价值投资理念的量化策略，主要通过筛选低估的大市值股票构建投资组合。策略定期筛选市值较大、估值较低且具有良好财务状况的股票，同时在盘中对已持有的股票进行动态调整。策略还通过邮件系统自动发送每月的选股信息和每周的持仓总结，方便投资者进行跟踪和管理。

### 核心代码及技术文档说明

1\. 初始化函数

```python
from jqdata import *
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import base64
def initialize(context):
    set_benchmark('000300.XSHG')  # 设置沪深300为基准指数
    set_option('use_real_price', True)  # 启用真实价格模式
    set_option("avoid_future_data", True)  # 避免使用未来数据
    log.info('初始函数开始运行且全局只运行一次')
    log.set_level('order', 'error')  # 仅记录error级别以上的日志
    # 股票参数
    g.buy_stock_count = 5  # 每次选股数量
    g.check_out_lists = []  # 当日筛选出的股票列表
    g.high_limit_list = []  # 昨日涨停的股票列表
    g.hold_list = []  # 当前持仓的股票列表
    # 邮件参数
    g.open_gmail = False  # 邮件功能开关
    g.gmail_host = "smtp.163.com"  # 邮箱服务器
    g.gmail_port = 25  # SMTP服务端口
    g.gmail_sender = 'xxxx@163.com'  # 发件人邮箱
    g.gmail_authcode = 'xxxx'  # 邮箱授权码
    g.gmail_receivers = ['xxxx@163.com', 'xxxx@qq.com']  # 收件人邮箱列表
    # 日常运行逻辑
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 开盘前准备股票池
    run_monthly(before_market_open, 1, time='9:05', reference_security='000300.XSHG')  # 每月初选股
    run_monthly(my_trade, 1, time='9:30', reference_security='000300.XSHG')  # 每月初执行调仓
    run_daily(check_limit_up, time='14:30', reference_security='000300.XSHG')  # 下午检查涨停股票
    run_monthly(send_to_mail, -1, time='15:10', reference_security='000300.XSHG')  # 每月发送邮件总结
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')  # 收盘后运行总结
```

技术说明：

  * **初始化** ：设定策略的全局参数和邮件功能，同时定义策略每日、每月的运行逻辑。

  * **实时价格与避免未来数据** ：开启真实价格模式并避免使用未来数据，确保策略回测和实盘的一致性。

2\. 股票池准备与选股逻辑

```python
def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]  # 获取当前持仓股票
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)  # 获取昨日涨停股票
    else:
        g.high_limit_list = []
def before_market_open(context):
    g.check_out_lists = []
    current_data = get_current_data()
    check_date = context.previous_date - datetime.timedelta(days=200)
    all_stocks = list(get_all_securities(date=check_date).index)
    # 筛选股票：剔除创业板、ST、停牌、涨停开盘、跌停开盘等股票
    all_stocks = [stock for stock in all_stocks if not (
            (current_data[stock].day_open == current_data[stock].high_limit) or
            (current_data[stock].day_open == current_data[stock].low_limit) or
            current_data[stock].paused or
            current_data[stock].is_st or
            ('ST' in current_data[stock].name) or
            ('*' in current_data[stock].name) or
            ('退' in current_data[stock].name) or
            (stock.startswith('30')) or  # 创业板
            (stock.startswith('68')) or  # 科创板
            (stock.startswith('8')) or  # 北交所
            (stock.startswith('4'))   # 北交所
    )]
    # 基于市值、估值和财务指标进行筛选
    q = query(
        valuation.code, valuation.market_cap, valuation.pe_ratio, income.total_operating_revenue
        ).filter(
        valuation.pb_ratio < 1,  # 市净率低于1
        cash_flow.subtotal_operate_cash_inflow > 1e6,  # 经营活动现金流入大于100万
        indicator.adjusted_profit > 1e6,  # 调整后净利润大于100万
        indicator.roa > 0.15,  # 资产回报率大于15%
        indicator.inc_net_profit_year_on_year > 0,  # 净利润同比增长为正
    	valuation.code.in_(all_stocks)
    	).order_by(
    	indicator.roa.desc()  # 按资产回报率降序排列
    ).limit(
    	g.buy_stock_count * 3
    )
    g.check_out_lists = list(get_fundamentals(q).code)[:g.buy_stock_count]
    log.info("今日股票池：%s" % g.check_out_lists)
    send_mail(context, g.check_out_lists, ["可买"] * len(g.check_out_lists), '大市值价值投资-本月筛选', '本月筛选股票')
```

技术说明：

  * **股票筛选** ：通过多维度的基本面筛选，包括市净率、现金流、净利润、资产回报率等指标，挑选出具备投资价值的大市值股票。

  * **过滤条件** ：剔除高风险股票，如ST股票、创业板股票、科创板股票等，确保投资组合的安全性。

3\. 调仓与交易逻辑

```python
def my_trade(context):
    adjust_position(context, g.check_out_lists)
def adjust_position(context, buy_stocks):
    sellbuystocklist = []
    advlist_s = []
    for stock in g.hold_list:
        if (stock not in buy_stocks) and (stock not in g.high_limit_list):
            log.info("卖出[%s]" % (stock))
            position = context.portfolio.positions[stock]
            sellbuystocklist.append(stock)
            advlist_s.append("卖出"+str(position.total_amount)+"股")
            close_position(position)
        else:
            log.info("已持有[%s]" % (stock))
    # 根据剩余仓位进行买入操作
    position_count = len(context.portfolio.positions)
    if g.buy_stock_count > position_count:
        value = context.portfolio.cash / (g.buy_stock_count - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    sellbuystocklist.append(stock)
                    advlist_s.append("买入"+str(context.portfolio.positions[stock].total_amount)+"股")
                    if len(context.portfolio.positions) == g.buy_stock_count:
                        break
    send_mail(context, sellbuystocklist, advlist_s, '大市值价值投资-调仓通知', '调仓通知')
```

技术说明：

  * **调仓逻辑** ：根据筛选出的股票池，对现有持仓进行调整，卖出不符合条件的股票，并买入新的优质股票。

  * **买卖规则** ：股票按资金平均分配，并优先选择未持有的股票进行买入。

4\. 邮件发送功能

```python
def send_mail(context, stocklist, advlist, title, info, sumup=""):
    if not g.open_gmail:
        return False
    host = g.gmail_host
    port = g.gmail_port
    sender = g.gmail_sender
    authcode = g.gmail_authcode
    receivers = g.gmail_receivers
    stockstr = ''
    for i, stock in enumerate(stocklist):
        stockcode = stock.split(".")[0]
        price_now = attribute_history(stock, 1, '1m', 'close')['close'][0]
        stockstr += f'{i+1}. {get_security_info(stock).display_name}: {stock}  最新价：{price_now}'\
                    f'{advlist[i]}  查看📖'
    mail_msg = f'{info}{str(context.current_dt)}股票列表: {stockstr}{sumup}'
    try:
        smtp = smtplib.SMTP(host, port)
        smtp.login(sender, authcode)
        for tomail in receivers:
            message = MIMEText(mail_msg, 'html', 'utf-8')
            fromnick = sender.split('@')[0]
            fromnickname64str = str(base64.b64encode(fromnick.encode()), 'utf-8')
            message['From'] = Header(f'"=?utf-8?B?{fromnickname64str}?=" <{sender}>')
            message['Subject'] = Header(title, 'utf-8')
            nickname64str = str(base64.b64encode(tomail.split('@')[0].encode()), 'utf-8')
            message['To'] = Header(f'"=?utf-8?B?{nickname64str}?=" <{tomail}>')
            smtp.sendmail(sender, [tomail], message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("Error: 无法发送邮件")
    finally:
        smtp.quit()
```

技术说明：

  * **邮件功能** ：自动发送筛选出的股票列表和调仓信息，方便投资者及时跟踪策略执行情况。

  * **邮件内容** ：包括股票代码、当前价格、操作建议等，确保信息全面且易于理解。

### 策略优势：

  * **价值投资** ：通过严格的基本面筛选，选择具有长期投资价值的大市值股票。

  * **动态调整** ：每月对股票池进行筛选，并根据市场情况动态调整持仓。

  * **信息透明** ：通过邮件系统及时发送选股和调仓信息，提高策略的透明度和可操作性。

### 总结：

**大市值价值投资策略** 通过结合基本面筛选和动态调整，力求在波动的市场中构建一个稳定而优质的投资组合。策略特别适合长期投资者，尤其是那些希望通过价值投资实现稳健收益的人士。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
