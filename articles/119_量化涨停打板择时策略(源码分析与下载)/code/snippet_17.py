# ==============================
# 参数（策略/市场/生成器 全局配置）
# ==============================
AUTO_POOL_SIZE_DEFAULT = 30   # 每次自动生成的股票池数量（默认30只）
ORDER_TIMEOUT_SEC = 120       # 下单后若在该秒数内未完全成交，则撤单（模拟排队超时）
MOMO_THRESHOLD = 0.02         # 动量阈值：近25个tick的涨幅需≥2%才算“动量足”
MAX_PRICE = 120.0             # 生成股票时的“昨收价”上限（过滤过高价）
MIN_PRICE = 3.0               # 生成股票时的“昨收价”下限（过滤仙股）
QUEUE_RATIO_CAP = 0.05        # 我方估算买单量 / 买一队列量 的上限（队列过小或我单过大则不下）
SEED = 20260101               # 随机种子（保证可复现）
def ensure_dir(p):
    """确保目录存在，不存在就创建"""
    if not os.path.exists(p):
        os.makedirs(p)
def now_str():
    """当前时间的字符串，用于打印日志前缀"""
    return datetime.now().strftime("%H:%M:%S")
def to_cent(p: float) -> int:
    """把价格转为“分”为单位的整数，便于做容差比较"""
    return int(round(p * 100))
def is_price_equal(a: float, b: float, tol_cent: int = 1) -> bool:
    """
    判断两个价格是否“近似相等”
    - tol_cent：允许的最大片差（单位：分），默认1分容差
    - 对涨停价这种边界价格，撮合/比较更稳健
    """
    return abs(to_cent(a) - to_cent(b)) <= tol_cent
# 仿真时间轴（仅用于生成假行情）
MARKET_OPEN = datetime(2025, 1, 1, 9, 30, 0)   # 开盘时间（模拟）
MARKET_CLOSE = datetime(2025, 1, 1, 10, 0, 0)  # 本示例只跑到 10:00

复制
