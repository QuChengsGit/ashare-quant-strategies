# 56、多因子深度学习量化选股策略

### 策略介绍：

**多因子深度学习量化选股策略** 是一种结合了多因子分析和深度学习模型的量化投资策略。该策略首先基于多因子模型进行初步筛选，筛选出符合一定基本面和技术面条件的股票；然后，利用预训练的深度学习模型进一步分析这些股票的特征，挑选出最有潜力的标的进行投资。策略在选股时考虑了多种技术指标和基本面数据，通过深度学习模型进一步提高了选股的精确度和收益预期。

### 核心代码及技术文档说明

1\. 初始化函数

```python
from jqdata import *
import torch
import torch.nn as nn
import pickle
import io
def initialize(context):
    set_benchmark('000985.XSHG')  # 设定中证全指为基准指数
    set_option('use_real_price', True)  # 启用真实价格交易模式
    set_option("avoid_future_data", True)  # 防止未来数据
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    log.set_level('order', 'error')  # 仅记录error级别以上的日志
    # 全局变量初始化
    g.no_trading_today_signal = False
    g.stock_num = 20  # 每次持仓的股票数量
    g.hold_list = []  # 当前持仓的股票列表
    g.yesterday_HL_list = []  # 昨日涨停的股票列表
    g.factor_list = [  # 因子列表
        "boll_down", "boll_up", "EMA5", "EMAC10", "EMAC12", "EMAC120",
        "EMAC20", "EMAC26", "MAC10", "MAC120", "MAC20", "MAC5",
        "MAC60", "MACDC", "MFI14", "price_no_fq"
    ]
    # 加载模型
    model_path1 = 'ZCSZX_0.pt'
    model_path2 = 'ZCSZX_1.pt'
    model_path3 = 'ZCSZX_2.pt'
    g.model1 = load_model(model_path1)
    g.model2 = load_model(model_path2)
    g.model3 = load_model(model_path3)
    # 设置交易运行时间
    run_daily(prepare_stock_list, '9:05')
    run_weekly(weekly_adjustment, 1, '9:30')
    run_daily(check_limit_up, '14:00')
    run_daily(close_account, '14:50')
def load_model(model_path):
    buffer = io.BytesIO(read_file(model_path))
    model = Model()
    model.load_state_dict(torch.load(buffer))
    model.eval()
    return model
class Model(nn.Module):
    def __init__(self, fc1_size=2000, fc2_size=1000, fc3_size=100, fc1_dropout=0.2, fc2_dropout=0.2, fc3_dropout=0.2):
        super(Model, self).__init__()
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
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
            nn.Conv1d(16, 32, kernel_size=1),
            nn.BatchNorm1d(32),
            nn.ReLU()
        )
        self.conv_2D = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=2),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            nn.Conv2d(16, 32, kernel_size=2),
            nn.BatchNorm2d(32),
            nn.ReLU()
        )
        self.lstm = nn.LSTM(input_size=32, hidden_size=32, num_layers=4, batch_first=True, bidirectional=True)
        for name, module in self.named_modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, mode='fan_in', nonlinearity='relu')
            if isinstance(module, nn.Conv2d):
                nn.init.kaiming_normal_(module.weight, mode='fan_in', nonlinearity='relu')
            if isinstance(module, nn.Conv1d):
                nn.init.kaiming_normal_(module.weight, mode='fan_in', nonlinearity='relu')
    def forward(self, x):
        x = (x - x.min(1, keepdim=True)[0]) / (x.max(1, keepdim=True)[0] - x.min(1, keepdim=True)[0] + 1e-5)
        xx = x.unsqueeze(1)
        xx = self.conv_2D(xx).view(xx.size(0), -1)
        x = self.conv_layers1(x.transpose(1, 2))
        out, _ = self.lstm(x.transpose(1, 2))
        out = out.view(out.size(0), -1)
        out = torch.cat((xx, out), dim=1)
        return self.f_model(out)
```

技术说明：

  * **深度学习模型** ：加载预训练的深度学习模型，用于股票的特征提取和评分。

  * **数据预处理与模型训练** ：模型通过卷积神经网络（CNN）和长短期记忆网络（LSTM）结合实现对股票历史数据的特征提取和趋势预测。

2\. 选股与持仓调整

```python
def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.yesterday_HL_list = df[df['close'] == df['high_limit']].code.tolist()
    else:
        g.yesterday_HL_list = []
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = filter_all_stock2(context, get_all_securities('stock', yesterday).index.tolist())
    factor_data = get_factor_values(initial_list, g.factor_list, end_date=yesterday, count=1)
    df_jq_factor_value = pd.DataFrame({factor: factor_data[factor].iloc[:, 0] for factor in g.factor_list}, index=initial_list)
    df_jq_factor_value = data_preprocessing(df_jq_factor_value, initial_list, industry_code, yesterday)
    tar = g.model1.predict_proba(df_jq_factor_value)[:, 1]
    df_jq_factor_value['total_score'] = tar
    df_jq_factor_value = df_jq_factor_value[df_jq_factor_value['total_score'] > 0.5].sort_values(by='total_score', ascending=False)
    positive_list = df_jq_factor_value.index.tolist()[:int(0.1 * len(df_jq_factor_value))]
    df_fundamentals = get_fundamentals(query(valuation.code, valuation.circulating_market_cap, indicator.eps)
                                        .filter(valuation.code.in_(positive_list))
                                        .order_by(valuation.circulating_market_cap.asc()))
    lst = df_fundamentals[df_fundamentals['eps'] > 0].code.tolist()
    lst = filter_paused_stock(lst)
    lst = filter_limitup_stock(context, lst)
    lst = filter_limitdown_stock(context, lst)
    tensor_list = [torch.Tensor(attribute_history(i, 60, '1d').values) for i in lst]
    stacked_tensor = torch.stack(tensor_list)
    with torch.no_grad():
        output1 = g.model1(stacked_tensor)
        output2 = g.model2(stacked_tensor)
        output3 = g.model3(stacked_tensor)
        output = output1 + output2 + output3
    data = {'ID': lst, 'score': output[:, 1].squeeze().tolist()}
    df = pd.DataFrame(data).nlargest(3, 'score')
    return df['ID'].tolist()
def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        for stock in g.hold_list:
            if stock not in target_list and stock not in g.yesterday_HL_list:
                log.info("卖出[%s]" % (stock))
                close_position
(context.portfolio.positions[stock])
        position_count = len(context.portfolio.positions)
        value = context.portfolio.cash / (len(target_list) - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value) and len(context.portfolio.positions) == len(target_list):
                    break
```

技术说明：

  * **多因子初筛** ：使用技术指标和基本面因子进行初步筛选，确定初选股票池。

  * **深度学习模型打分** ：利用深度学习模型对筛选出的股票进行进一步打分，挑选出得分最高的股票作为最终目标持仓。

  * **持仓调整** ：每周定期调整持仓，卖出不再符合条件的股票，买入新的优质股票。

3\. 辅助函数与风险控制

```python
def filter_all_stock2(context, stock_list):
    by_date = get_trade_days(end_date=context.previous_date, count=180)[0]
    all_stocks = get_all_securities(date=by_date).index.tolist()
    stock_list = list(set(stock_list).intersection(set(all_stocks)))
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (
            stock.startswith(('3', '68', '4', '8')) or  # 创业板、科创板、北交所
            curr_data[stock].paused or curr_data[stock].is_st or
            ('ST' in curr_data[stock].name) or ('*' in curr_data[stock].name) or
            ('退' in curr_data[stock].name) or
            curr_data[stock].day_open == curr_data[stock].high_limit or
            curr_data[stock].day_open == curr_data[stock].low_limit
    )]
def order_target_value_(security, value):
    log.debug("Order %s to value %f" % (get_security_info(security).display_name, value))
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    order = order_target_value_(position.security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount
```

技术说明：

  * **股票过滤** ：剔除ST股、创业板股票、科创板股票以及其他高风险股票，确保投资组合的安全性。

  * **开仓与平仓** ：根据筛选结果调整持仓，确保投资组合符合策略要求。

### 策略优势：

  * **深度学习模型** ：策略引入深度学习模型，提高了选股精确度，能够更好地捕捉市场趋势。

  * **多因子筛选** ：结合多因子模型与深度学习，筛选出具有较高增长潜力的股票。

  * **动态调整** ：定期调整持仓，确保投资组合始终保持最优状态。

### 总结：

**多因子深度学习量化选股策略** 通过结合多因子模型和深度学习，显著提高了选股的准确性和收益预期，适合在复杂市场环境中实现稳健增长。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
