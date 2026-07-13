class stock:
    def __init__(self, df, window_size=6):
        self.n_actions = 3  # 动作数量：买入、卖出、保持
        self.n_features = window_size  # 特征数量：滑动窗口大小
        self.trend = df['close'].values  # 收盘价
        self.trend_open = df['open'].values  # 开盘价
        self.window_size = window_size  # 滑动窗口大小
        self.hold_num = 0  # 持仓状态：0表示空仓，1表示持仓
    def step(self, action):
        # 根据动作更新持仓状态
        if action == 1:  # 买入
            self.hold_num = 1
        if action == 2:  # 卖出
            self.hold_num = 0
        # 计算当前收益
        reward = (self.trend[self.t + 1] - self.trend[self.t]) / self.trend[self.t]
        # 根据收益的幅度调整奖励值
        if np.abs(reward) <= 0.015:
            self.reward = reward * 0.2
        elif np.abs(reward) <= 0.03:
            self.reward = reward * 0.7
        elif np.abs(reward) >= 0.05:
            if reward < 0:
                self.reward = (reward + 0.05) * 0.1 - 0.05
            else:
                self.reward = (reward - 0.05) * 0.1 + 0.05
        # 根据持仓状态和动作调整奖励值
        if self.hold_num > 0 or action == 2:
            self.reward = reward
            if action == 2:
                self.reward = -self.reward
        else:
            self.reward = -self.reward * 0.1
        # 更新时间步
        done = False
        self.t = self.t + 1
        if self.t == len(self.trend) - 2:
            done = True
        s_ = self.get_state(self.t)
        reward = self.reward
        return s_, reward, done
    def get_state(self, t):  # 获取当前状态
        window_size = self.window_size + 1
        d = t - window_size + 1
        block = []
        if d < 0:
            for i in range(-d):
                block.append(self.trend[0])
            for i in range(t + 1):
                block.append(self.trend[i])
        else:
            block = self.trend[d: t + 1]
        res = []
        for i in range(window_size - 1):
            res.append((block[i + 1] - block[i]) / (block[i] + 0.0001))  # 计算滑动窗口内的收益
        return np.array(res)  # 返回作为状态的特征向量
    def reset(self):
        self.total_profit = 0  # 总盈利
        self.t = self.window_size // 2  # 时间步初始化
        self.reward = 0  # 初始奖励
        return self.get_state(self.t)

复制
