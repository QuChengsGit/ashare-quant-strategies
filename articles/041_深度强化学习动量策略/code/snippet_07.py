max_round = 100  # 训练轮数
net = DQN(6, 3)  # 初始化网络
net.train()
tgt_net = DQN(6, 3)
tgt_net.train()
# 训练超参数设置
learn_step_counter = 0
replace_target_iter = 200
batch_size = 512
lr = 0.001
gamma = 0.9
epsilon = 200
epsilon_increment = None
epsilon_max = 0.9
memory_size = 4000
n_features = 6
optimizer = optim.Adam(net.parameters(), lr=lr)
# 训练过程
for episode in tqdm(range(max_round)):
    observation = env.reset()
    l = 0
    r = 0
    memory_counter = 0
    memory = np.zeros((memory_size, n_features * 2 + 2))
    while True:
        Observation = [observation[np.newaxis, :]]
        Observation = torch.tensor(Observation, dtype=torch.float32).to(device)
        actions_value = net(Observation).detach().cpu().squeeze(0)
        action = np.argmax(actions_value)
        observation_, reward, done = env.step(action)
        r = r + reward
        transition = np.hstack((observation, [action, reward], observation_))
        # 存储记忆
        index = memory_counter % memory_size
        memory[index, :] = transition
        memory_counter += 1
        if learn_step_counter % replace_target_iter == 0:
            tgt_net.load_state_dict(net.state_dict())
        if memory_counter > memory_size:
            sample_index = np.random.choice(memory_size, size=batch_size)
        else:
            sample_index = np.random.choice(memory_counter, size=batch_size)
        batch_memory = memory[sample_index, :]
        s_ = torch.tensor(batch_memory[:, -n_features:], dtype=torch.float32).to(device)
        s = torch.tensor(batch_memory[:, :n_features], dtype=torch.float32).to(device)
        eval_act_index = batch_memory[:, n_features].astype(int)
        reward = torch.tensor(batch_memory[:, n_features + 1], dtype=torch.float32)
        q_next = tgt_net(s_)
        q_eval = net(s)
        q_target = q_eval.clone()
        batch_index = np.arange(batch_size, dtype=np.int32)
        max_, _ = torch.max(q_next, dim=1)
        q_target[batch_index, eval_act_index] = reward + gamma * max_
        optimizer.zero_grad()
        loss = nn.MSELoss()(q_eval, q_target)
        loss.backward()
        optimizer.step()
        epsilon = epsilon + epsilon_increment if epsilon < epsilon_max else epsilon_max
        learn_step_counter += 1
        observation = observation_
        if done:
            break
        step += 1
        l += loss.detach().cpu().numpy()

复制
