# 51、增强型量价因子自适应策略

### 策略介绍：

**增强型量价因子自适应策略** 是一种结合了交易量和价格因子进行预测的量化交易策略。通过对历史数据中的量价关系进行分析，提取出有助于预测未来收益的特征（因子），并利用先进的机器学习模型进行训练，生成预测结果。策略通过严格的回测流程验证其有效性，并结合实验记录管理器（如Qlib）进行模型管理和性能评估。此策略的特点是自适应性强，能够根据市场变化动态调整因子权重，从而实现更高的收益率。

### 核心代码及技术文档说明

1\. 数据获取与预处理

```python
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
```

技术说明：

  * **数据获取** ：利用 get_ts_etf_price 和 get_ts_index_price 获取指定时间段内的ETF及基准指数数据，包括开盘价、收盘价、最高价、最低价、成交量和成交金额等。

  * **数据处理** ：对获取到的数据进行必要的单位转换和列重命名，以确保数据的一致性和正确性。

  * **数据保存** ：按股票代码将数据分组并保存为CSV文件，方便后续的模型训练和预测使用。

2\. Qlib初始化与数据加载

```python
import qlib
from qlib.workflow import R  # 实验记录管理器
from qlib.constant import REG_CN
from qlib.workflow.record_temp import SignalRecord, SigAnaRecord
# 初始化Qlib
qlib.init(provider_uri="qlib_etf_data", region=REG_CN)
# 加载ETF行业数据
industry_etf: pd.DataFrame = pd.read_csv(
    '../行业有效量价因子/qlib_etf_data/instruments/industry_etf.txt',
    delimiter='\t', header=None, parse_dates=[1, 2]
)
industry_etf.columns = ['symbol', 'begin_dt', 'end_dt']
# 数据可视化分析
industry_etf["begin_dt"].dt.year.value_counts().sort_index().plot.bar()
industry_etf["begin_dt"].dt.year.value_counts().div(
    len(industry_etf)
).sort_index().cumsum().plot(marker='o')
plt.show()
```

技术说明：

  * **Qlib初始化** ：通过 qlib.init 初始化数据服务，指定数据存储路径和市场区域。

  * **数据加载** ：从指定路径加载ETF行业数据，并进行初步的时间分布分析，以确定数据的有效性和分布特征。

  * **可视化分析** ：通过柱状图和累计分布图展示ETF数据的时间分布，帮助量化分析师了解数据集的整体情况。

3\. 参数配置

```python
# 定义训练、验证、测试的时间段
TRAIN_PERIODS: Tuple = ("2014-01-01", "2017-12-31")
VALID_PERIODS: Tuple = ("2018-01-01", "2020-12-31")
TEST_PERIODS: Tuple = ("2021-01-01", "2023-02-17")
# 数据处理器参数配置
data_handler_config: Dict = {
    "start_time": TRAIN_PERIODS[0],
    "end_time": TEST_PERIODS[1],
    "fit_start_time": TRAIN_PERIODS[0],
    "fit_end_time": TRAIN_PERIODS[1],
    "instruments": "market",
}
# 任务配置：模型与数据集
task: Dict = {
    "model": {
        "class": "LGBModel",
        "module_path": "qlib.contrib.model.gbdt",
        "kwargs": {
            "loss": "mse",
            "colsample_bytree": 0.8,
            "learning_rate": 0.05,
            "subsample": 0.85,
            "lambda_l1": 100.0,
            "lambda_l2": 200.0,
            "max_depth": 10,
            "num_leaves": 64,
            "num_threads": 8,
            "early_stopping_rounds": 100,
            "num_boost_round": 500,
        },
    },
    "dataset": {
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                "class": "VolumePriceFactor192",
                "module_path": "scr.factor_expr",
                "kwargs": data_handler_config,
            },
            "segments": {
                "train": TRAIN_PERIODS,
                "valid": VALID_PERIODS,
                "test": TEST_PERIODS,
            },
        },
    },
}
```

技术说明：

  * **时间段划分** ：策略按照训练、验证和测试阶段将数据集划分为三个时间段，确保模型在训练期间没有看到测试数据，避免数据泄漏。

  * **数据处理器配置** ：设置数据处理器的时间范围、股票池等参数，定义处理器如何读取和处理原始数据。

  * **模型与数据集配置** ：通过任务配置定义模型类型、超参数设置以及数据集配置，确保策略能够有效利用量价因子进行预测。

4\. 模型训练与预测

```python
from qlib.utils import init_instance_by_config
import pickle
# 实例化模型与数据集
model = init_instance_by_config(task["model"])
dataset = init_instance_by_config(task["dataset"])
# 保存数据集以便后续使用
dataset.config(dump_all=True, recursive=True)
dataset.to_pickle(path="dataset.pkl", dump_all=True)
# 加载保存的数据集
with open("dataset.pkl", "rb") as file_dataset:
    dataset = pickle.load(file_dataset)
# 准备数据集并划分训练、验证和测试集
df_train, df_valid, df_test = dataset.prepare(segments=["train", "valid", "test"], data_key="raw")
# 模型训练与实验记录
with R.start(experiment_name="train"):
    R.log_params(**task)
    model.fit(dataset)
    R.save_objects(trained_model=model)
# 生成预测结果并进行信号分析
with R.start(experiment_name="predict"):
    predict_recorder = R.get_recorder()
    sig_rec = SignalRecord(model, dataset, predict_recorder)
    sig_rec.generate()
    sigAna_rec = SigAnaRecord(predict_recorder)
    sigAna_rec.generate()
```

技术说明：

  * **模型与数据集实例化** ：使用配置参数实例化模型和数据集，为后续的训练和预测做好准备。

  * **数据集保存与加载** ：将数据集保存为文件，并在需要时加载，方便后续的策略复现和分析。

  * **数据准备与划分** ：使用 prepare 方法将数据集划分为训练、验证和测试集，确保模型能够在不同阶段评估其性能。

  * **模型训练与记录** ：通过 Qlib 的实验管理工具 R 进行模型训练，记录训练过程中的所有参数和模型对象，便于后续分析。

  * **预测与信号分析** ：使用训练好的模型生成预测结果，并进行信号分析，评估模型在测试集上的表现。

### 策略优势：

  * **自适应性** ：策略能够根据市场的动态变化调整因子权重，使模型在不同市场环境下都能表现良好。

  * **严格回测** ：通过将数据集划分为训练

、验证和测试集，并使用独立的测试集进行模型评估，确保策略具有较强的泛化能力。

  * **透明度与可重复性** ：通过 Qlib 的实验管理器记录所有实验过程和结果，保证了策略的透明性和可重复性。

### 总结：

**增强型量价因子自适应策略** 结合了量价因子的优势，并利用先进的机器学习模型进行训练和预测，通过自适应机制实现了在不同市场环境下的稳定表现，是一种具有较高实际应用价值的量化交易策略。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
