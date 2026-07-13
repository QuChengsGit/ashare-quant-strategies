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

复制
