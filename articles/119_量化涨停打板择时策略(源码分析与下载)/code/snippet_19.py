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

复制
