# 67、智能深度学习选股策略

### 策略介绍

**智能深度学习选股策略** 是一种融合深度学习模型与量化选股方法的先进策略。该策略利用神经网络模型（包括CNN和LSTM层）对股票历史数据进行特征提取，通过训练好的模型预测股票的未来表现。同时，策略结合传统的量化分析方法对选股结果进行调整，并通过严格的风控措施确保策略的稳健性。策略每日自动选出最优的股票组合，并定期调整持仓，旨在实现长期稳定的收益。

### 核心代码及技术文档说明

1\. 初始化与全局变量设置

```python
from jqdata import *
from jqfactor import *
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
def initialize(context):
    set_benchmark('000985.XSHG')  # 设定中证全指为基准
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    log.set_level('order', 'error')
    g.no_trading_today_signal = False
    g.stock_num = 3  # 持股数量上限
    g.hold_list = []  # 当前持仓列表
    g.yesterday_HL_list = []  # 昨日涨停股列表
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00')
    run_daily(close_account, '14:50')
```

技术说明：

  * **初始化函数** ：设置策略的基本配置，包括基准指数、滑点、交易成本和日志等级。通过全局变量管理持仓、选股和风控信号。

  * **调度函数** ：策略在每天和每周的指定时间运行各模块，确保及时的选股和调仓。

2\. 深度学习模型加载与推理

```python
class model(nn.Module):
    def __init__(self, fc1_size=2000, fc2_size=1000, fc3_size=100, fc1_dropout=0.2, fc2_dropout=0.2, fc3_dropout=0.2):
        super(model, self).__init__()
        self.f_model = nn.Sequential(
            nn.Linear(2816, fc1_size),
            nn.BatchNorm1d(fc1_size),
            nn.ReLU(),
            nn.Dropout(fc1_dropout),
            nn.Linear(fc1_size, fc2_size),
            nn.BatchNorm1d(fc2_size),
            nn.ReLU(),
            nn.Dropout(fc2_dropout),
            nn.Linear(fc2_size, fc3_size),
            nn.BatchNorm1d(fc3_size),
            nn.ReLU(),
            nn.Dropout(fc3_dropout),
            nn.Linear(fc3_size, 2)
        )
        self.conv_layers1 = nn.Sequential(
            nn.Conv1d(6, 16, kernel_size=1),
            nn.BatchNorm1d(16),
            nn.Dropout(fc3_dropout),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
            nn.Conv1d(16, 32, kernel_size=1),
            nn.BatchNorm1d(32),
            nn.Dropout(fc3_dropout),
            nn.ReLU()
        )
        self.conv_2D = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=2),
            nn.BatchNorm2d(16),
            nn.Dropout(fc3_dropout),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            nn.Conv2d(16, 32, kernel_size=2),
            nn.BatchNorm2d(32),
            nn.Dropout(fc3_dropout),
            nn.ReLU()
        )
        hidden_dim = 32
        self.lstm = nn.LSTM(input_size=hidden_dim, hidden_size=hidden_dim, num_layers=4, batch_first=True, bidirectional=True)
    def forward(self, x):
        min_vals, _ = torch.min(x, dim=1, keepdim=True)
        max_vals, _ = torch.max(x, dim=1, keepdim=True)
        x = (x - min_vals) / (max_vals - min_vals + 0.00001)
        xx = x.unsqueeze(1)
        xx = self.conv_2D(xx)
        xx = torch.reshape(xx, (xx.shape[0], xx.shape[1] * xx.shape[2] * xx.shape[3]))
        x = x.transpose(1, 2)
        x = self.conv_layers1(x)
        out2, _ = self.lstm(x.transpose(1, 2))
        out2 = torch.reshape(out2, (out2.shape[0], out2.shape[1] * out2.shape[2]))
        out = self.f_model(torch.cat((xx, out2), dim=1))
        return out
# 加载模型
model_path1 = 'ZCSZX_0.pt'
model_path2 = 'ZCSZX_1.pt'
model_path3 = 'ZCSZX_2.pt'
model_t1 = torch.load(model_path1)
model_t2 = torch.load(model_path2)
model_t3 = torch.load(model_path3)
model_t1.eval()
model_t2.eval()
model_t3.eval()
```

技术说明：

  * **模型架构** ：结合卷积神经网络（CNN）和长短期记忆网络（LSTM），对股票的时序数据进行深度特征提取。

  * **模型加载** ：从本地加载预训练的模型参数，并设置为评估模式，以便在推理过程中进行预测。

3\. 选股与调仓逻辑

```python
def get_stock_list(context):
    yesterday = context.previous_date
    today = context.current_dt
    initial_list = get_all_securities('stock', today).index.tolist()
    initial_list = filter_all_stock2(context, initial_list)
    tensor_list = []
    for i in initial_list:
        df = attribute_history(i, 60, '1d')
        df_tensor = torch.Tensor(df.values)
        tensor_list.append(df_tensor)
    stacked_tensor = torch.stack(tensor_list)
    with torch.no_grad():
        output1 = model_t1(stacked_tensor)
        output2 = model_t2(stacked_tensor)
        output3 = model_t3(stacked_tensor)
        output = output1 + output2 + output3
        output = output[:, 1]
    data = {'ID': initial_list, 'score': output.squeeze().tolist()}
    df = pd.DataFrame(data)
    top_N_rows = df.nlargest(g.stock_num, 'score')
    top_N_IDs = top_N_rows['ID'].tolist()
    return top_N_IDs
def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        for stock in g.hold_list:
            if stock not in target_list and stock not in g.yesterday_HL_list:
                position = context.portfolio.positions[stock]
                close_position(position)
        position_count = len(context.portfolio.positions)
        target_num = len(target_list)
        if target_num > position_count:
            value = context.portfolio.cash / (target_num - position_count)
            for stock in target_list:
                if context.portfolio.positions[stock].total_amount == 0:
                    if open_position(stock, value):
                        if len(context.portfolio.positions) == target_num:
                            break
```

技术说明：

  * **选股逻辑** ：模型通过对历史60天的股票数据进行处理，输出每只股票的得分，选择得分最高的股票进入持仓。

  * **调仓逻辑** ：每周进行一次持仓调整，清仓表现不佳的股票，买入模型评分最高的股票。

4\. 风控与辅助模块

```python
def check_limit_up(context):
    now_time = context.current_dt
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                position = context.portfolio.positions[stock]
                close_position(position)
def close_account(context):
    if g.no_trading_today_signal and g.hold_list:
        for stock in g.hold_list:
            position = context.portfolio.positions[stock]
            close_position(position)
```

技术说明：

  * **风控策略** ：在每日收盘前检查涨停股票，如果涨停被打开则立即卖出，以避免次日可能的风险。

  * **清仓逻辑** ：在特定信号触发时，清空所有持仓，确保资金安全。

### 策略优势

  * **深度学习驱动** ：通过深度学习模型对股票数据进行高效的特征提取与

预测，提升选股精度。

  * **动态调仓** ：结合传统量化选股方法与深度学习，实时调整持仓，确保策略的灵活性。

  * **风控严谨** ：通过严格的风控措施，避免因市场波动或意外事件造成的损失。

### 总结

**智能深度学习选股策略** 通过结合前沿的深度学习模型与传统量化策略，提供了一种面向未来的投资解决方案。该策略在控制风险的同时，追求稳定的收益增长，适用于追求长期收益的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
