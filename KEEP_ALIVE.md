# 防止 Render 服务休眠指南

Render 的免费实例会在 15 分钟无活动后自动休眠。首次请求需要 30-60 秒唤醒。以下是几种保持服务活跃的方案。

## 方案一：UptimeRobot（推荐）⭐

**优点**：
- 完全免费
- 配置简单
- 可靠稳定
- 支持多种监控类型

### 设置步骤

1. **注册账号**
   - 访问 https://uptimerobot.com
   - 使用邮箱注册（免费账号支持 50 个监控）

2. **添加监控**
   - 登录后点击 "Add New Monitor"
   - **Monitor Type**: 选择 "HTTP(s)"
   - **Friendly Name**: `Quatre-Vingt Backend`（任意名称）
   - **URL**: 输入你的 Render 服务 URL
     - 例如：`https://your-app.onrender.com/health`
   - **Monitoring Interval**: 选择 `5 minutes`（最短间隔）
   - 点击 "Create Monitor"

3. **完成**
   - UptimeRobot 会每 5 分钟访问一次你的服务
   - 服务将保持活跃，不会休眠

### 使用健康检查端点

确保你的后端有健康检查端点（已有）：

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

UptimeRobot 会访问这个端点，不会影响游戏逻辑。

---

## 方案二：GitHub Actions（免费）

**优点**：
- 完全免费
- 不需要第三方服务
- 代码托管在 GitHub

### 设置步骤

1. **创建 GitHub Actions 工作流**

   在项目根目录创建 `.github/workflows/keep-alive.yml`：

```yaml
name: Keep Render Alive

on:
  schedule:
    # 每 10 分钟运行一次（UTC 时间）
    - cron: '*/10 * * * *'
  workflow_dispatch: # 允许手动触发

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Render Service
        run: |
          curl -f https://your-app.onrender.com/health || exit 1
```

2. **替换 URL**
   - 将 `your-app.onrender.com` 替换为你的实际 Render URL

3. **提交代码**
   ```bash
   git add .github/workflows/keep-alive.yml
   git commit -m "Add keep-alive workflow"
   git push
   ```

4. **启用 Actions**
   - 在 GitHub 仓库设置中启用 GitHub Actions
   - 工作流会自动运行

**注意**：GitHub Actions 的免费额度是每月 2000 分钟，每 10 分钟运行一次，每月约 4320 次，完全够用。

---

## 方案三：其他免费监控服务

### Pingdom
- 网址：https://www.pingdom.com
- 免费版：1 个监控，每 5 分钟检查一次

### StatusCake
- 网址：https://www.statuscake.com
- 免费版：10 个监控，每 5 分钟检查一次

### Better Uptime
- 网址：https://betteruptime.com
- 免费版：10 个监控，每 30 秒检查一次

---

## 方案四：本地终端脚本（适合临时测试）

### 方法 A：使用提供的脚本

项目已包含 `keep-alive.sh` 脚本：

```bash
# 使用默认设置（5分钟间隔）
./keep-alive.sh https://your-app.onrender.com/health

# 自定义间隔（例如 10 分钟 = 600 秒）
./keep-alive.sh https://your-app.onrender.com/health 600
```

### 方法 B：使用 watch 命令

```bash
# 每 5 分钟（300 秒）执行一次
watch -n 300 'curl -s https://your-app.onrender.com/health'
```

### 方法 C：使用 while 循环

```bash
# 在终端运行（会一直运行，按 Ctrl+C 停止）
while true; do
  curl -f https://your-app.onrender.com/health
  sleep 300  # 等待 5 分钟（300 秒）
done
```

### 方法 D：使用 cron（Linux/macOS）

如果你有自己的服务器，可以创建一个 cron 任务：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每 5 分钟执行一次）
*/5 * * * * curl -f https://your-app.onrender.com/health > /dev/null 2>&1
```

**注意**：本地终端脚本需要你的电脑一直运行。如果电脑关机，监控会停止。

---

## 推荐方案对比

| 方案 | 难度 | 可靠性 | 推荐度 | 说明 |
|------|------|--------|--------|------|
| UptimeRobot | ⭐ 简单 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 最佳选择，完全免费 |
| GitHub Actions | ⭐⭐ 中等 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 代码托管，无需第三方 |
| 本地脚本 | ⭐ 简单 | ⭐⭐ | ⭐⭐ | 仅适合临时测试，需电脑常开 |
| Pingdom | ⭐ 简单 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 免费版有限制 |
| StatusCake | ⭐ 简单 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 免费版有限制 |

## 最佳实践

1. **使用健康检查端点**
   - 不要 ping 游戏 API（可能触发游戏逻辑）
   - 使用 `/health` 端点（轻量级）

2. **监控间隔**
   - 建议 5-10 分钟
   - Render 休眠时间是 15 分钟
   - 5 分钟间隔可以确保服务始终活跃

3. **监控多个端点**（可选）
   - 主服务：`/health`
   - WebSocket：可以 ping 主服务（WebSocket 会自动保持连接）

4. **设置告警**（可选）
   - 如果服务下线，UptimeRobot 会发送邮件通知
   - 可以帮助你及时发现问题

---

## 验证是否生效

部署监控后，可以通过以下方式验证：

1. **查看 Render 日志**
   - 在 Render 控制台查看日志
   - 应该能看到每 5-10 分钟有健康检查请求

2. **测试休眠**
   - 停止监控 20 分钟
   - 访问服务，应该需要 30-60 秒才能响应（休眠唤醒）
   - 重新启用监控后，服务应该立即响应

---

## 注意事项

1. **不要过于频繁**
   - 虽然 Render 没有明确限制，但过于频繁的请求可能被视为滥用
   - 建议间隔 5-10 分钟

2. **监控成本**
   - 所有推荐的方案都是免费的
   - 不会产生额外费用

3. **备用方案**
   - 如果主要监控服务失效，可以考虑使用多个监控服务
   - 或者使用 GitHub Actions 作为备用

---

## 快速开始（推荐）

**最简单的方法**：使用 UptimeRobot

1. 访问 https://uptimerobot.com
2. 注册账号
3. 添加监控：`https://your-app.onrender.com/health`
4. 设置间隔：5 分钟
5. 完成！

就这么简单，服务将保持活跃，不会休眠。

