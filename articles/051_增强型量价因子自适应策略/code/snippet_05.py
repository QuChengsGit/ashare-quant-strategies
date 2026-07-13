import sys
from pathlib import Path
import pandas as pd
from scr.data_service import get_ts_etf_price, get_ts_index_price
# 路径设置与模块导入
this_file_path = Path().resolve()
sys.path.append(str(this_file_path.parents[0]))
# 获取ETF和基准指数的历史数据
etf_price: pd.DataFrame = get_ts_etf_price(
    start_date="2014-01-01",
    end_date="2023-02-17",
    fields=["open", "high", "low", "close", "vol", "amount"],
)
# 数据预处理：转换单位与重命名
etf_price['volume'] = etf_price['vol'] * 100
etf_price['amount'] = etf_price['amount'] * 1000
etf_price.rename(columns={"vol": "volume"}, inplace=True)
etf_price["factor"] = 1  # 设置初始因子值
# 获取基准指数数据
benchmark: pd.DataFrame = get_ts_index_price(
    "000300.SH",
    start_date="2014-01-01",
    end_date="2023-02-17",
    fields=["open", "high", "low", "close", "volume", "amount"],
)
# 数据预处理：转换单位与设置初始因子
benchmark['volume'] *= 100
benchmark['amount'] *= 1000
benchmark['factor'] = 1
# 合并数据并保存为CSV文件
data_all: pd.DataFrame = pd.concat((etf_price, benchmark))
ETF_PRICE_PATH: str = "../行业有效量价因子/etf_price"
for code, df in data_all.groupby('code'):
    csv_name: str = f"{code.split('.')[1]}{code.split('.')[0].upper()}.csv"
    df.to_csv(ETF_PRICE_PATH / csv_name, index=False)

复制
