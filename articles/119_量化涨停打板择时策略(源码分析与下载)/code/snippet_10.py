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
