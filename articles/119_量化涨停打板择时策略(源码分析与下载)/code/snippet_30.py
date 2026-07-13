# ==============================
# 策略（信号与下单）
# ==============================
class StrategyState:
    """策略内部状态：已买标记 + 每票tick缓存（用于动量/回封识别）"""
    def __init__(self):
        self.bought_list = set()                           # 已经触发下单的股票，防重复
        self.data_cache = defaultdict(lambda: deque(maxlen=100))  # 每票最近100个tick
def calc_momo_25tick(cache: deque, thres=MOMO_THRESHOLD):
    """
    25个tick动量过滤： (现价 - 25tick前价格) / 25tick前价格 ≥ 阈值
    - tick频率由市场生成器决定（此处用秒级），只是相对窗口
    """
    if len(cache) < 25: return False
    start = cache[-25]['lastPrice']
    last = cache[-1]['lastPrice']
    return (last - start) / max(start, 1e-6) >= thres
def calc_refill_signal(cache: deque, limit_price: float):
    """
    回封信号：过去30个tick中出现过“低于涨停价”，且当前价=涨停价
    - 简易识别“炸板后回封”的事件
    """
    if len(cache) < 30: return False
    lim = to_cent(limit_price)
    prices = [to_cent(x['lastPrice']) for x in list(cache)[-30:]]
    was_below = any(p < lim for p in prices)        # 曾低于涨停
    now_at = is_price_equal(cache[-1]['lastPrice'], limit_price)  # 当前在涨停
    return was_below and now_at
def queue_ok(sd: dict, limit_price: float, buy_values: float):
    """
    队列合理性过滤：
      - 买一价必须等于涨停价（封单存在）
      - 买一队列量q>0
      - 估算我方下单量 ≤ 买一队列量 * QUEUE_RATIO_CAP
    目的：避免在队列过薄/自己过大时盲目排队，提升可成交概率。
    """
    if not sd.get('bidPrice') or not sd.get('bidVol'):
        return False
    if not is_price_equal(sd['bidPrice'][0], limit_price):
        return False
    q = sd['bidVol'][0]
    if q <= 0:
        return False
    # 估算我方下单量（按最新价把 buy_values 转成股数，向下取整到“手”）
    est_my = int(buy_values // max(sd['lastPrice'], 0.01))
    est_my = (est_my // 100) * 100
    if est_my <= 0:
        return False
    return est_my / max(q, 1) <= QUEUE_RATIO_CAP
def calc_volume(lastprice, buy_values):
    """把‘每笔金额’换算为股数（向下取整到100的倍数）"""
    cnt = int(buy_values // max(lastprice, 0.01))
    vol = (cnt // 100) * 100
    return max(0, vol)
