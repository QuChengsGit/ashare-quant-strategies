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
