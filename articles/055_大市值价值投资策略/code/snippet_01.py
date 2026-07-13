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
