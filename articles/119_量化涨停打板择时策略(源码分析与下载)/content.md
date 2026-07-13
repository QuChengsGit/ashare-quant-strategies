# 119、量化涨停打板择时策略（源码分析与下载）

# 策略专业介绍

该策略面向 A 股日内高动量场景，核心思想是：在 09:30–10:00 的交易早盘时段，捕捉触及涨停且满足回封（炸板后再度封回）或短窗动量的标的；同时通过买一封单队列合理性约束（我方估算下单量相对于买一队列量的上限）来提高成交可得性与风控质量。撮合端采用本地模拟撮合内核，将“买一封单量 × 近期吃单比例”作为可成交上限，支持限时撤单（超时未成自动撤）。标的池、涨停价字典与行情全量模拟，确保无外部依赖、可复现实验。**本文策略的完整代码下载地址请见文末最下方。**



## 1）文件头与模块导入

```python
# sim_limit_up_strategy.py
# -*- coding: utf-8 -*-
"""
打板策略
- 行情：一字→炸板→回封，含买一封单与被吃速度（用于模拟封单消化速度）
- 策略：09:30–10:00 触板 + 回封/动量过滤 + 队列合理性；限价(涨停价)排队，超时撤单
- 兼容 Notebook：忽略未知参数（如 ipykernel 注入的 -f kernel.json）
"""
import os
import sys
import json
import time
import random
import threading
import argparse
import configparser
from datetime import datetime, timedelta
from collections import deque, defaultdict
```

说明（逐行）：

  * # sim_limit_up_strategy.py：文件名注释，便于溯源与运行定位。

  * # -*- coding: utf-8 -*-：源文件编码声明，确保中文注释/字符串在不同环境下可读。

  * 三引号字符串块：模块级文档，简述策略特性与兼容性注意点。

  * import os：文件/路径操作（生成/写入配置与池文件）。

  * import sys：保留系统参数等（虽未显式使用，但与 Notebook 兼容场景常用）。

  * import json：读写涨停价字典 JSON 文件。

  * import time：主循环中微睡眠，降低 CPU 占用。

  * import random：生成股票池、行情、价格/队列的随机化模拟。

  * import threading：账户更新时加锁，保障并发安全。

  * import argparse：命令行参数解析，兼容 parse_known_args。

  * import configparser：读写 ini 配置（qmt_path、账号、每笔金额）。

  * from datetime import datetime, timedelta：时间戳、窗口推进与比较。

  * from collections import deque, defaultdict：高效队列缓存与默认字典（持仓/均价/缓存）。



## 2）全局参数与工具函数、仿真时钟

```python
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
```

说明（逐行）：

  * 常量块：统一集中参数，便于回测/实验调参（池规模、撤单时限、动量阈值、价格过滤、队列占比上限、随机种子）。

  * ensure_dir：若目录不存在则创建，保证“配置文件”目录可写。

  * now_str：统一日志时间格式。

  * to_cent：价格转分，避免浮点误差导致的等值判断问题。

  * is_price_equal：允许 1 分容差的价等判断，更贴近撮合实务。

  * MARKET_OPEN/CLOSE：模拟盘的时窗，行情生成的时间参考。



## 3）配置文件读写

```python
# ==============================
# 配置文件读写（兼容无配置时自动生成）
# ==============================
def load_config():
    """
    读取 ./配置文件/config.ini：
      - Path.qmt_path        仅用于打印展示（与模拟撮合无强绑定）
      - Account.stock_account 同上
      - Trading.buy_values   每笔下单金额（元）
    若文件缺失，自动写入一份默认配置。
    """
    cfg_file = './配置文件/config.ini'
    if not os.path.exists(cfg_file):
        ensure_dir('./配置文件')
        cfg = configparser.ConfigParser()
        # 这些项主要用于保持与原始策略脚本的字段一致
        cfg['Path'] = {'qmt_path': r'C:\QMT\userdata'}
        cfg['Account'] = {'stock_account': 'SIM123456'}
        cfg['Trading'] = {'buy_values': '20000'}
        with open(cfg_file, 'w', encoding='utf-8') as f:
            cfg.write(f)
    cfg = configparser.ConfigParser()
    cfg.read(cfg_file, encoding='utf-8')
    path = cfg.get('Path', 'qmt_path', fallback=r'C:\QMT\userdata')
    stock_account = cfg.get('Account', 'stock_account', fallback='SIM123456')
    buy_values = cfg.getint('Trading', 'buy_values', fallback=20000)
    print(f"[{now_str()}] 读取配置完成 path={path} account={stock_account} buy_values={buy_values}")
    return path, stock_account, buy_values
```

说明（逐行）：

  * cfg_file：固定路径存放策略配置。

  * 若文件不存在：创建目录、写入默认配置（保持与“原 xtquant 风格”的字段名一致）。

  * 读取配置：按节-键获取值，提供 fallback 以防缺项。

  * 打印读取结果：便于核对运行环境与每笔买入金额。

  * 返回三元组：后续主程序与日志使用。



## 4）股票池自动生成（每次覆盖）

```python
# ==============================
# 自动股票池（每次运行都覆盖现有文件）
# ==============================
def _gen_code_range(exchange: str, start_num: int, end_num: int, k: int) -> list:
    """
    在给定六位数字区间内随机抽样 k 个股票代码，并拼上交易所前缀：
      例：exchange='SH'，start_num=600000 → 'SH600000'
    - 仅负责生成“形如 SH600000/SZ300123”的字符串，不负责真伪有效性校验
    """
    nums = list(range(start_num, end_num + 1))
    random.shuffle(nums)           # 打乱以保证抽样随机
    sel = nums[:k]                 # 取前k个作为样本
    return [f"{exchange}{n:06d}" for n in sel]
def _board_of(code: str) -> str:
    """
    根据六位数字判断板块：
      - 300xxx → GEM20（创业板，涨跌幅20%）
      - 688xxx → STAR20（科创板，涨跌幅20%）
      - 其他   → MAIN10（主板/中小板，涨跌幅10%）
    用于后续生成“昨收价→涨停价”的映射时选择涨幅比例。
    """
    num = int(code[-6:])
    if 300000 <= num <= 399999:
        return "GEM20"
    if 688000 <= num <= 699999:
        return "STAR20"
    return "MAIN10"
def _auto_generate_pool(target_size: int) -> list:
    """
    生成目标规模的混合股票池（主板/创业/科创分布），并覆盖写回 ./配置文件/股票池.txt
    - 通过设置随机价位+流动性打分进行简单质量筛选
    - 注意：仅用于模拟；真实环境请替换为交易标的筛选逻辑（量能/波动/题材等）
    """
    random.seed(SEED)
    # 候选区间（覆盖常见编码段；并非真实全量代码表）
    cand_main = []
    # 上交所主板
    cand_main += _gen_code_range("SH", 600000, 600999, 200)
    cand_main += _gen_code_range("SH", 601000, 601999, 200)
    # 深市主板/中小
    cand_main += _gen_code_range("SZ", 100, 999, 200)      # 000100~000999
    cand_main += _gen_code_range("SZ", 2000, 2999, 200)    # 002000~002999
    # 创业板
    cand_gem  = _gen_code_range("SZ", 300001, 300999, 300) # 300001~300999
    # 科创板
    cand_star = _gen_code_range("SH", 688001, 688999, 200) # 688001~688999
    def synth_attrs(code):
        """
        为候选合成两个属性：
          - px  ：模拟昨收价（不同板块给不同价位范围）
          - liq ：模拟“流动性分数”（0~1，越大越活跃）
        并据此做一次基本过滤（MIN_PRICE~MAX_PRICE）
        """
        b = _board_of(code)
        px = round(random.uniform(5, 50), 2) if b == "MAIN10" else round(random.uniform(8, 90), 2)
        liq = random.random()
        ok = (MIN_PRICE <= px <= MAX_PRICE)
        return ok, px, liq
    # 目标配比：主板 ~70%，创业 ~18%，科创 ~12%
    tgt_main = int(target_size * 0.70)
    tgt_gem  = int(target_size * 0.18)
    tgt_star = target_size - tgt_main - tgt_gem
    def pick_from(cands, need):
        """对候选计算(liq)并按流动性降序选出 need 个"""
        rows = []
        for c in cands:
            ok, px, liq = synth_attrs(c)
            if ok:
                rows.append((c, px, liq))
        rows.sort(key=lambda x: x[2], reverse=True)
        return [r[0] for r in rows[:need]]
    # 按配比抽取
    pool = []
    pool += pick_from(cand_main, tgt_main)
    pool += pick_from(cand_gem,  tgt_gem)
    pool += pick_from(cand_star, tgt_star)
    # 若因过滤导致不足，则从剩余里补齐
    if len(pool) < target_size:
        rest = []
        for c in (cand_main + cand_gem + cand_star):
            ok, px, liq = synth_attrs(c)
            if ok:
                rest.append((c, px, liq))
        random.shuffle(rest)
        for c, _, _ in rest:
            if len(pool) >= target_size: break
            if c not in pool: pool.append(c)
    # 最终按字典序排序，便于阅读与diff
    pool = sorted(pool[:target_size])
    # 覆盖写入到文件（方便外部查看）
    ensure_dir('./配置文件')
    with open('./配置文件/股票池.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(pool) + "\n")
    print(f"[{now_str()}] 已自动生成股票池并覆盖写入：./配置文件/股票池.txt")
    print(f"[{now_str()}] 股票池示例：{pool[:8]}{'...' if len(pool)>8 else ''}（共{len(pool)}只）")
    return pool
def load_stock_pool_always_regen(target_size: int):
    """外部接口：始终重建股票池（忽略现有文件内容）"""
    return _auto_generate_pool(target_size)
```

说明要点：

  * _gen_code_range：按区间随机抽样，拼交易所前缀，统一六位数字格式。

  * _board_of：根据数段判板块（决定后续涨停幅 10%/20%）。

  * _auto_generate_pool：

    * 先生成按交易所/编码段的候选，再合成“昨收价/流动性分数”。

    * 按目标配比（70/18/12）筛选，若不足再补齐。

    * 最后覆盖写入 股票池.txt，并返回内存列表。

  * load_stock_pool_always_regen：对外的统一入口（每次强制重建）。



## 5）涨停价字典（缺码自动补齐）

```python
# ==============================
# 涨停价字典（若存在但缺码则补齐写回）
# ==============================
def load_limit_up_dict(code_list):
    """
    读取 ./配置文件/{YYYYMMDD}-limit_up_prices.json
    - 若文件存在但缺少当前股票池里的代码，则为缺口生成涨停价并写回文件；
    - 若文件不存在，则对当前股票池整包生成。
    这里的“昨收价→涨停价”仅为模拟（MAIN10按10%计算，GEM/STAR按20%计算）。
    """
    today_str = datetime.now().strftime('%Y%m%d')
    path = f'./配置文件/{today_str}-limit_up_prices.json'
    def gen_limit_for(code):
        """给单个股票按板块规则生成一个涨停价（基于随机昨收价）"""
        b = _board_of(code)
        if b == "MAIN10":
            last_close = round(random.uniform(5, 50), 2)
            return round(last_close * 1.10, 2)
        else:
            last_close = round(random.uniform(8, 90), 2)
            return round(last_close * 1.20, 2)
    if os.path.exists(path):
        # 情形A：有文件——>读入并补齐缺码
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        missing = [c for c in code_list if c not in d]
        if missing:
            print(f"[{now_str()}] 发现涨停价字典缺少 {len(missing)} 只代码，自动补齐并写回。")
            random.seed(SEED + 7)
            for c in missing:
                d[c] = float(gen_limit_for(c))
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
        else:
            print(f"[{now_str()}] 读取涨停价字典完成（来自文件）")
        return d, today_str
    # 情形B：无文件——>整包生成
    print(f"[{now_str()}] 未找到涨停价文件，自动生成：{path}")
    random.seed(SEED + 7)
    d = {c: float(gen_limit_for(c)) for c in code_list}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d, today_str
```

说明要点：

  * 当日维度文件名（YYYYMMDD），便于日切。

  * 已存在则补缺；不存在则整包生成。

  * 生成逻辑：主板按 1.10，创业/科创按 1.20，从随机昨收价推导（纯模拟）。



## 6）模拟撮合内核（订单、账户、回调、撮合器）

```python
# ==============================
# 模拟撮合/回调（最小可用撮合内核）
# ==============================
class SimOrder:
    """模拟的订单对象：仅支持限价买入"""
    def __init__(self, order_id, code, side, price, volume, remark, ts):
        self.order_id = order_id    # 订单编号（自增）
        self.code = code            # 股票代码
        self.side = side            # BUY/SELL（本策略仅用BUY）
        self.price = price          # 限价（策略里=涨停价）
        self.volume = volume        # 委托股数
        self.remark = remark        # 备注（方便日志）
        self.created_at = ts        # 下单时间戳（datetime）
        self.filled_volume = 0      # 已成交数量
        self.canceled = False       # 是否已撤
        self.done = False           # 是否已完成（完全成交）
class SimAccount:
    """模拟账户：仅记录现金+持仓+均价，并在成交时更新"""
    def __init__(self, cash=1_000_000.0):
        self.cash = cash
        self.positions = defaultdict(int)   # code -> 持股数
        self.avg_cost = defaultdict(float)  # code -> 持仓均价
        self.lock = threading.Lock()        # 线程安全（撮合回调与主循环可能并行）
    def on_trade(self, code, price, vol, side):
        """成交回写账户：买入扣现金、更新均价；（若有卖出则加现金/减仓）"""
        with self.lock:
            if side == 'BUY':
                cost = price * vol
                self.cash -= cost
                pos = self.positions
                new_pos = pos + vol
                # 新均价 = (旧成本 + 本次成本) / 新持仓
                self.avg_cost = (self.avg_cost * pos + cost) / new_pos if pos > 0 else price
                self.positions = new_pos
            else:
                # 这里未使用SELL，但保留逻辑以便扩展
                self.cash += price * vol
                self.positions -= vol
                if self.positions <= 0:
                    self.positions = 0
                    self.avg_cost = 0.0
class SimTraderCallback:
    """
    “柜台”回调接口（空实现），外部策略可继承覆写以打印日志等
    - on_order_stock_async_response：异步接单回报
    - on_stock_trade：逐笔成交回报
    - on_stock_order：订单完成（全部成交）可视作委托完成通知
    - on_cancel_order_stock_async_response：撤单结果
    """
    def on_stock_order(self, order): pass
    def on_stock_trade(self, code, price, volume, order): pass
    def on_order_stock_async_response(self, order): pass
    def on_cancel_order_stock_async_response(self, order): pass
class SimTrader:
    """
    极简撮合器：
    - 仅撮合“买入@涨停价”的限价单；
    - 成交量由“买一队列量 * 近期吃单比例”上限决定；
    - 按到达顺序遍历订单分配可成交量；
    - 订单超时未完全成交会被撤销（ORDER_TIMEOUT_SEC）。
    """
    def __init__(self, account: SimAccount, cb: SimTraderCallback, order_timeout_sec=ORDER_TIMEOUT_SEC):
        self.acc = account
        self.cb = cb
        self.order_timeout = order_timeout_sec
        self._id = 0
        self.orders = {}             # oid -> SimOrder
        self.lock = threading.Lock() # 下单/访问订单字典的并发保护
    def order_stock_async(self, code, side, price, volume, remark, ts):
        """异步下单：分配订单号，写入订单簿，并回调“已受理”"""
        with self.lock:
            self._id += 1
            oid = self._id
            od = SimOrder(oid, code, side, price, volume, remark, ts)
            self.orders[oid] = od
        if self.cb:
            self.cb.on_order_stock_async_response(od)
        return oid
    def cancel_if_timeout(self, now_ts):
        """
        撤单扫描：若订单自创建起超过 order_timeout 仍未完成，则设置为已撤，并发回撤单回报
        - 模拟真实环境中“排队超时撤单”的风险控制动作
        """
        for od in list(self.orders.values()):
            if od.done or od.canceled:
                continue
            if (now_ts - od.created_at).total_seconds() >= self.order_timeout:
                od.canceled = True
                if self.cb:
                    self.cb.on_cancel_order_stock_async_response(od)
    def try_match(self, code, limit_price, buy1_queue_vol, recent_fill_ratio, tick_ts):
        """
        撮合：在当前tick内，对所有“code 且 限价=涨停价 且 未撤/未完”的BUY订单进行匹配
        - can_fill_total = buy1_queue_vol * recent_fill_ratio
        - 逐单分配：每单能吃多少吃多少，直到“可吃总量”耗尽
        """
        # 过滤出可参与本次撮合的订单
        live = [od for od in self.orders.values()
                if (od.code == code and (not od.done) and (not od.canceled)
                    and od.side == 'BUY' and is_price_equal(od.price, limit_price))]
        if not live:
            return
        # 本tick可消化的总量（由封单量与近期吃单速度决定）
        can_fill_total = int(max(0, recent_fill_ratio * buy1_queue_vol))
        for od in live:
            if can_fill_total <= 0:
                break
            want = od.volume - od.filled_volume
            if want <= 0:
                od.done = True
                continue
            # 实际成交量 = min(订单剩余需求, 本tick剩余可吃量)
            fill = min(want, can_fill_total)
            if fill > 0:
                od.filled_volume += fill
                can_fill_total -= fill
                # 写回账户与回调成交
                self.acc.on_trade(od.code, limit_price, fill, od.side)
                if self.cb:
                    self.cb.on_stock_trade(od.code, limit_price, fill, od)
                # 若订单完全成交，回调“委托完成”
                if od.filled_volume >= od.volume:
                    od.done = True
                    if self.cb:
                        self.cb.on_stock_order(od)
```

说明要点：

  * SimOrder：撮合的基本单位，记录状态流转（受理→撮合→成交/撤单）。

  * SimAccount：仅做现金与持仓核算，均价按“加权平均”更新。

  * SimTraderCallback：事件回调接口（打印日志或接收撮合事件）。

  * SimTrader：

    * order_stock_async：下单即“受理”；

    * cancel_if_timeout：按创建时间判断是否超时撤；

    * try_match：可成交量上限设为“买一队列 × 吃单比例”，按单逐个分配。



## 7）行情引擎（上行→炸板→回封）

```python
# ==============================
# 行情引擎（生成一字→炸板→回封的状态机）
# ==============================
class SimMarket:
    """
    对每只股票维护一个“状态字典”：
      - price：当前价
      - bidPrice[0]/bidVol[0]：涨停价买一与其队列量
      - recent_queue_shrink：近期封单吃单比例（用于撮合端估算可成交量）
      - opened_from_limit / refilled：是否经历过炸板/回封
    规则：
      09:30–09:40   上行至涨停并形成封单
      09:40–09:50   炸板（回落，封单减少）
      09:50–10:00   回封（回到涨停，封单增加，设置recent_queue_shrink）
    """
    def __init__(self, code_list, limit_up_dict):
        self.codes = code_list
        self.limit = limit_up_dict
        self.last_close = {}
        self.state = {}
        random.seed(SEED + 99)
        for c in self.codes:
            lim = self.limit[c]
            # 用板块涨幅反推“昨收价”（纯模拟，不影响策略判断）
            lc = round(lim / 1.10, 2) if _board_of(c) == "MAIN10" else round(lim / 1.20, 2)
            self.last_close[c] = lc
            self.state[c] = {
                "price": lc,
                "bidPrice": [lim, lim - 0.01, lim - 0.02, lim - 0.03, lim - 0.05],
                "bidVol":   [0, 0, 0, 0, 0],
                "recent_queue_shrink": 0.0,
                "opened_from_limit": False,
                "refilled": False,
            }
    def gen_tick(self, tick_ts: datetime):
        """
        生成当前时刻的“市场切片”：
        - 为每只股票产出 lastPrice / bidPrice / bidVol 等字段
        - 这些字段会被策略与撮合联动使用
        """
        data = {}
        for c in self.codes:
            lim = self.limit[c]
            st = self.state[c]
            lc = self.last_close[c]
            # Phase1：上行至涨停形成封单（早盘拉升，买一队列逐步变厚）
            if tick_ts < MARKET_OPEN + timedelta(minutes=10):
                st["price"] = min(lim, st["price"] + random.uniform(0.02, 0.08))
                base_q = 30000 + int((tick_ts - MARKET_OPEN).total_seconds() / 2)
                st["bidPrice"][0] = lim
                st["bidVol"][0] = max(0, base_q + random.randint(-5000, 5000))
            # Phase2：炸板（价格回落，封单被吃，买一队列减少）
            elif tick_ts < MARKET_OPEN + timedelta(minutes=20):
                open_off = random.uniform(0.05, 0.4)           # 距涨停的回落幅度
                st["price"] = max(lim - open_off, lc * 0.95)  # 不跌破昨收95%
                st["bidVol"][0] = max(0, st["bidVol"][0] - random.randint(3000, 12000))
                st["opened_from_limit"] = True
            # Phase3：回封（回到涨停，封单回补加厚；并设定“封单吃单比例”）
            else:
                st["price"] = lim
                st["bidVol"][0] = max(10000, st["bidVol"][0] + random.randint(2000, 15000))
                st["recent_queue_shrink"] = random.uniform(0.05, 0.4)  # 0.05~0.4 的“可吃比例”
                if st["opened_from_limit"]:
                    st["refilled"] = True
            # 为买二~买五设置一个简单的阶梯价（仅用于展示/策略校验）
            st["bidPrice"][1] = max(lc, lim - 0.01)
            st["bidPrice"][2] = max(lc, lim - 0.02)
            st["bidPrice"][3] = max(lc, lim - 0.03)
            st["bidPrice"][4] = max(lc, lim - 0.05)
            # 输出到“行情切片”
            data[c] = {
                "time": tick_ts.strftime("%H:%M:%S"),
                "lastPrice": round(st["price"], 2),
                "open": lc,
                "high": max(lc, st["price"]),
                "low": min(lc, st["price"]),
                "lastClose": lc,
                "amount": 0, "volume": 0, "pvolume": 0, "stockStatus": 0,
                "askPrice": [], "bidPrice": st["bidPrice"][:],
                "askVol": [],   "bidVol":   st["bidVol"][:],
            }
        return data
```

说明要点：

  * 三段行情演化：形成封单→炸板→回封；recent_queue_shrink 为撮合端的“吃单比例”输入。

  * bidPrice 阶梯价仅用于展示/校验，不参与真实撮合（只有买一用到）。



## 8）策略信号与下单

```python
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
```

说明要点：

  * StrategyState：两大结构——已买集合防止重复、每票 deque 做近窗因子计算。

  * calc_momo_25tick：25 tick 动量过滤。

  * calc_refill_signal：回封事件识别（近 30 tick 曾破涨停且当前等于涨停）。

  * queue_ok：封单合理性（买一在涨停、队列正、我单不超过队列占比上限）。

  * calc_volume：把“每笔购买金额”转换为“手”为单位的股数。



## 9）柜台回调与策略主控

```python
class MyCallback(SimTraderCallback):
    """覆写回调：打印关键撮合事件"""
    def on_stock_order(self, order):
        print(f"[{now_str()}] 委托完成 代码={order.code} 成交={order.filled_volume}/{order.volume} 备注={order.remark}")
    def on_stock_trade(self, code, price, volume, order):
        print(f"[{now_str()}] 成交回报 {code} 价={price:.2f} 量={volume} 订单={order.order_id} 备注={order.remark}")
    def on_order_stock_async_response(self, order):
        print(f"[{now_str()}] 异步委托回调 已受理 订单={order.order_id} {order.code} {order.volume}@{order.price:.2f} {order.remark}")
    def on_cancel_order_stock_async_response(self, order):
        print(f"[{now_str()}] 撤单回报 订单={order.order_id} {order.code} 已撤（超时或未成）")
class StrategyRunner:
    """
    策略主控：
      - 接收行情tick，更新缓存
      - 在涨停价处进行三重过滤（队列/回封或动量）
      - 通过撮合器下单并跟踪成交/撤单
    """
    def __init__(self, code_list, limit_up_dict, buy_values):
        self.state = StrategyState()
        self.codes = code_list
        self.limit = limit_up_dict
        self.buy_values = buy_values
        self.account = SimAccount(cash=1_000_000.0)
        self.trader = SimTrader(self.account, MyCallback(), order_timeout_sec=ORDER_TIMEOUT_SEC)
        self.market = SimMarket(self.codes, self.limit)
    def on_tick(self, data, tick_ts):
        """每个tick的策略执行：仅在 09:30~10:00 时间窗内触发"""
        if not (MARKET_OPEN.time() <= tick_ts.time() <= MARKET_CLOSE.time()):
            return
        for code, sd in data.items():
            # 非池内或已下过单的股票跳过
            if (code not in self.codes) or (code in self.state.bought_list):
                continue
            # 维护该票的最近tick缓存
            self.state.data_cache.append(sd)
            # 仅在当前价=涨停价时考虑打板
            lim = self.limit.get(code)
            if not lim or not is_price_equal(sd['lastPrice'], lim):
                continue
            # 三重过滤：队列合理性 + （回封信号 或 25tick动量）
            ok_queue = queue_ok(sd, lim, self.buy_values)
            sig_refill = calc_refill_signal(self.state.data_cache, lim)
            sig_momo = calc_momo_25tick(self.state.data_cache, thres=MOMO_THRESHOLD)
            if not (ok_queue and (sig_refill or sig_momo)):
                continue
            # 计算下单量（按 buy_values/现价、取整到手）
            vol = calc_volume(sd['lastPrice'], self.buy_values)
            if vol < 100:
                continue
            # 以“涨停价”限价买入；下单后将该票加入“已买”以免重复下单
            _ = self.trader.order_stock_async(code, side='BUY', price=lim, volume=vol,
                                              remark='打板策略-限价涨停', ts=tick_ts)
            self.state.bought_list.add(code)
        # 对存量未完成订单执行“超时撤单”
        self.trader.cancel_if_timeout(tick_ts)
    def match_engine_step(self, data, tick_ts):
        """
        将当期“买一封单”和“封单吃单速度”同步给撮合器，驱动撮合成交
        - buy1_queue_vol：买一队列量
        - recent_fill_ratio：近期吃单比例（SimMarket里生成）
        """
        for code, sd in data.items():
            lim = self.limit.get(code)
            if not lim:
                continue
            buy1_q = sd['bidVol'][0] if (sd.get('bidVol') and len(sd['bidVol'])>0) else 0
            recent_ratio = self.market.state["recent_queue_shrink"]
            recent_ratio = max(0.01, recent_ratio)  # 给最低吃单比例，避免完全“冻住”
            self.trader.try_match(code, lim, buy1_q, recent_ratio, tick_ts)
    def run(self):
        """主循环：从 09:20 生成行情到 10:00，逐秒推送tick并驱动策略/撮合"""
        tick_ts = MARKET_OPEN - timedelta(minutes=10)  # 从 09:20 开始（预热阶段）
        end_ts = MARKET_CLOSE
        print(f"[{now_str()}] 模拟启动：{tick_ts.strftime('%H:%M:%S')} → {end_ts.strftime('%H:%M:%S')}")
        step = timedelta(seconds=1)
        while tick_ts <= end_ts:
            data = self.market.gen_tick(tick_ts)  # 生成当前tick市场切片
            self.on_tick(data, tick_ts)          # 策略逻辑（可能触发下单/撤单）
            self.match_engine_step(data, tick_ts)# 传入封单与吃单比例以尝试撮合
            tick_ts += step
            time.sleep(0.005)                    # 小睡降低CPU占用（纯模拟）
        # 收盘概览
        print("\n========== 模拟收盘 ==========")
        print(f"现金余额：{self.account.cash:.2f}")
        any_pos = False
        for code, pos in self.account.positions.items():
            if pos > 0:
                any_pos = True
                print(f"{code} 持仓 {pos} 股，成本 {self.account.avg_cost:.2f}")
        if not any_pos:
            print("(当日无成交/持仓)")
        print("================================\n")
```

说明要点：

  * MyCallback：封装撮合回调输出，便于观察下单→成交/撤单链路。

  * StrategyRunner.__init__：组装策略四要素：状态、代码池、涨停价、账户/撮合器/行情引擎。

  * on_tick：

    * 时间窗过滤；

    * 价等于涨停价时才考虑；

    * 三重判定（队列合理性 +（回封 或 动量））；

    * 量化下单量并下单；加入已买集合；

    * 最后做一次“超时撤单”扫描。

  * match_engine_step：把市场端的“买一量/吃单比例”喂给撮合器，完成撮合。

  * run：逐秒推进 tick，调用行情生成→策略→撮合；收盘打印账户概览。



## 10）入口（参数解析与主程序）

```python
# ==============================
# 入口（命令行参数解析 & 主程序）
# ==============================
def parse_args():
    """
    仅支持 --pool-size 参数；其余 Notebook 注入参数将被忽略（parse_known_args）
    - 这样在 Jupyter/VSCode-Notebook 里直接运行不会报错
    """
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--pool-size", type=int, default=AUTO_POOL_SIZE_DEFAULT,
                    help=f"股票池规模（默认 {AUTO_POOL_SIZE_DEFAULT}）")
    args, _ = ap.parse_known_args()   # 忽略未知参数（如 -f kernel.json）
    return args
def main():
    """主程序：加载配置 → 生成股票池 → 生成/补齐涨停价 → 启动策略"""
    args = parse_args()
    ensure_dir('./配置文件')
    path, stock_account, buy_values = load_config()
    code_list = load_stock_pool_always_regen(args.pool_size)   # 每次都重建股票池
    limit_up_dict, today_str = load_limit_up_dict(code_list)
    runner = StrategyRunner(code_list, limit_up_dict, buy_values)
    runner.run()
if __name__ == '__main__':
    main()
```

说明要点（逐行）：

  * parse_args：仅定义 --pool-size，并使用 parse_known_args 忽略 Notebook 注入参数，提升环境兼容性。

  * main：流程编排：确保目录 → 读配置 → 重建股票池 → 读/补涨停字典 → 构建并运行策略。

  * if __name__ == '__main__':：脚本直接运行的入口。



# 总结

  1. 信号触发：仅在涨停价发生时才评估（避免噪声），并结合回封或短窗动量两类证据。

  2. 可成交性评估：queue_ok 约束我单在买一队列里的占比，有助于减少“排不动”的下单。

  3. 撮合与风控：以“封单×吃单比例”为可成交上限，带超时撤单，贴近实盘风控流程。

  4. 可复现实验：所有随机过程固定 SEED；股票池与涨停字典可复现且可落盘。

  5. 模块化：行情引擎/撮合内核/策略主控分离，便于将来替换真实行情/真柜台或扩展更多因子与风控。

**本文策略完整代码下载地址**

**链接：** https://pan.quark.cn/s/f79fcb4f8145

**提取码：** GdPU

**如果您想将文中的策略转换为适配QMT/Ptrade的代码，可以使用下面的转换工具：**

https://vxqn28ptbw.coze.site/
