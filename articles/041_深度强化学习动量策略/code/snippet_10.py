if min_validation_loss > l:
        min_validation_loss = l
        best_epoch = episode
        print('Min loss ' + str(min_validation_loss) + ' in epoch ' + str(best_epoch))
        torch.save(net.state_dict(), 'tgt_net.pt')
    LOSS.append(l)
    REWORD.append(r)
# 绘制损失和奖励变化图
x_values = np.arange(len(LOSS))
plt.plot(x_values, LOSS)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss Over Epochs')
plt.show()
plt.plot(x_values, REWORD)
plt.xlabel('Epoch')
plt.ylabel('Reward')
plt.title('Training Reward Over Epochs')
plt.show()
