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
