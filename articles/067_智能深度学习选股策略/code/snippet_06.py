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

复制
