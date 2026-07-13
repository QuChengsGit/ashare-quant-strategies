import pandas as pd
from typing import Dict, List
# 读取数据
data: pd.DataFrame = pd.read_csv('data/data.csv', index_col=[0,1], parse_dates=[0])

复制
