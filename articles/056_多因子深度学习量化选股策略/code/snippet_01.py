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
