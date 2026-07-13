import numpy as np
import pandas as pd
from scipy.linalg import solve
def initialize(context):
    set_benchmark('000300.XSHG')  # 设置基准指数为沪深300
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免使用未来数据进行回测
    set_slippage(FixedSlippage(0.002))  # 设置固定滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0002, close_commission=0.0002, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('system', 'error')  # 设置日志级别为错误
    g.etf_pool = [
        '518880.XSHG',  # 黄金ETF（大宗商品）
        '513100.XSHG',  # 纳指100（海外资产）
        '159915.XSHE',  # 创业板100（成长股，科技股，中小盘）
        '510880.XSHG',  # 红利ETF（价值股，蓝筹股，中大盘）
    ]
    run_monthly(trade, 1, '10:00')  # 每月10点执行交易函数，确保动态捕捉市场变化

复制
