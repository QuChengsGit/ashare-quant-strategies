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
