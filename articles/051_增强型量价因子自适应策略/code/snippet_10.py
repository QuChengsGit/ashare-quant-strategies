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

复制
