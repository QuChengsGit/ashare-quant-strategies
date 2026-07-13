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

复制
