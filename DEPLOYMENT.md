# 部署指南

本指南将帮助你将八十分游戏部署到互联网上。

## 架构概览

- **后端**: FastAPI (Python) - 需要支持 WebSocket
- **前端**: Vue 3 (Vite) - 静态文件部署

## 推荐部署方案

### 方案一：Railway（推荐） + Vercel

**优点**：
- Railway 完美支持 Python 和 WebSocket
- Vercel 对 Vue 3 支持极佳
- 两者都有免费额度
- 配置简单

### 方案二：Render + Vercel

**优点**：
- Render 支持 Python 和 WebSocket
- 免费额度充足
- 配置相对简单

---

## 部署步骤

### 第一步：部署后端（Railway）

1. **注册 Railway 账号**
   - 访问 https://railway.app
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库

3. **配置服务**
   - Railway 会自动检测到 `backend` 目录
   - 如果没有，在设置中指定 Root Directory 为 `backend`

4. **设置环境变量**
   在 Railway 项目设置中添加：
   ```
   ALLOWED_ORIGINS=["https://your-frontend-domain.vercel.app"]
   HOST=0.0.0.0
   PORT=$PORT
   DEBUG=False
   SECRET_KEY=your-random-secret-key-here
   ```

5. **配置启动命令**
   Railway 会自动检测，但可以手动设置：
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

6. **获取后端 URL**
   - Railway 会提供一个域名，例如：`your-app.railway.app`
   - 记下这个 URL，后续配置前端时需要

### 第二步：部署前端（Vercel）

1. **注册 Vercel 账号**
   - 访问 https://vercel.com
   - 使用 GitHub 账号登录

2. **导入项目**
   - 点击 "Add New Project"
   - 选择你的 GitHub 仓库
   - Framework Preset 选择 "Vite"

3. **配置项目设置**
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **设置环境变量**
   在 Vercel 项目设置中添加：
   ```
   VITE_API_URL=https://your-backend.railway.app
   VITE_WS_URL=wss://your-backend.railway.app
   ```

5. **部署**
   - 点击 "Deploy"
   - 等待部署完成
   - 获取前端 URL，例如：`your-app.vercel.app`

### 第三步：更新后端 CORS 配置

回到 Railway，更新环境变量：
```
ALLOWED_ORIGINS=["https://your-app.vercel.app"]
```

重新部署后端。

---

## 配置前端环境变量

需要修改前端代码以使用环境变量：

1. 创建 `frontend/.env.production`:
```env
VITE_API_URL=https://your-backend.railway.app
VITE_WS_URL=wss://your-backend.railway.app
```

2. 更新前端代码中的硬编码 URL（见下方代码修改）

---

## 代码修改

### 1. 更新前端 API 和 WebSocket URL

需要将硬编码的 `127.0.0.1:8000` 替换为环境变量。

### 2. 更新后端 CORS 配置

确保 `allowed_origins` 包含你的前端域名。

---

## 测试部署

1. 访问前端 URL
2. 创建房间
3. 邀请朋友加入
4. 测试游戏功能

---

## 其他部署选项

### Render（后端替代方案）

#### Render Web Service 详细配置

1. **访问 Render**
   - 访问 https://render.com
   - 使用 GitHub 账号登录

2. **创建新服务**
   - 点击 "New +" → 选择 "Web Service"
   - 连接你的 GitHub 仓库

3. **配置服务信息**
   - **Name**: `quatre-vingt-backend`（或你喜欢的名称）
   - **Language**: `Python 3`（Render 会自动检测）
   - **Branch**: `main`（或你的主分支）
   - **Region**: `Oregon (US West)`（或离你最近的区域）
   - **Root Directory**: `backend` ⚠️ **重要**：必须填写

4. **配置构建和启动命令**
   - **Build Command**: `pip install -r requirements.txt`
     - 或留空（Render 会自动检测并安装依赖）
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - ⚠️ **重要**：必须使用 `$PORT`（Render 动态分配的端口）

5. **设置环境变量**
   点击 "Add Environment Variable" 添加：
   ```
   ALLOWED_ORIGINS=["https://your-frontend.vercel.app"]
   DEBUG=False
   SECRET_KEY=生成一个随机字符串（至少32个字符）
   ```
   
   **注意**：
   - `ALLOWED_ORIGINS` 使用 JSON 数组格式
   - 例如：`["https://your-app.vercel.app","https://www.your-domain.com"]`
   - 多个域名用逗号分隔，整个用方括号包裹

6. **选择实例类型**
   - **Free**: 512MB RAM, 0.1 CPU（**足够使用**，见下方内存分析）
   - 免费实例会在 15 分钟无活动后休眠
   - 首次请求唤醒需要 30-60 秒

7. **部署**
   - 点击 "Create Web Service"
   - Render 会自动构建和部署
   - 获取后端 URL，例如：`your-app.onrender.com`

#### Render Free Tier 说明

**规格**：
- 512MB RAM
- 0.1 CPU
- 无活动时自动休眠（15 分钟）

**是否足够？** ✅ **完全足够**

根据内存分析（见 `MEMORY_ANALYSIS.md`）：
- 单局游戏内存占用：< 100KB
- Python 运行时：60-100 MB
- **总内存占用：约 60-100 MB**
- **剩余空间：400-450 MB**

即使同时运行 **50-100 个房间**（200-400 名玩家），内存也远低于 512MB。

**注意事项**：
- 免费实例会在无活动时休眠
- 首次请求需要 30-60 秒唤醒
- 可以使用免费监控服务（如 UptimeRobot）每 10 分钟 ping 一次保持活跃
- 如需无休眠，可升级到 Starter（$7/月）

**如果超过 512MB 会发生什么？**
- 进程会被系统杀死（OOM）
- 服务自动重启
- 用户会看到连接错误
- 建议监控内存使用，必要时升级

详细内存分析请查看 `MEMORY_ANALYSIS.md`。

### Netlify（前端替代方案）

1. 访问 https://netlify.com
2. 导入 GitHub 仓库
3. 配置构建设置：
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/dist`

---

## 注意事项

1. **WebSocket 协议**：
   - 生产环境必须使用 `wss://`（WebSocket Secure）
   - HTTP 环境使用 `ws://`，HTTPS 环境使用 `wss://`

2. **CORS 配置**：
   - 确保后端允许前端域名
   - 支持凭据传递（`allow_credentials=True`）

3. **环境变量**：
   - 不要将敏感信息提交到代码仓库
   - 使用各平台的环境变量功能

4. **域名绑定**：
   - Railway 和 Vercel 都支持自定义域名
   - 可以绑定自己的域名

---

## 故障排查

### WebSocket 连接失败
- 检查 URL 是否正确（`wss://` vs `ws://`）
- 检查后端 CORS 配置
- 查看浏览器控制台错误

### CORS 错误
- 确保后端 `ALLOWED_ORIGINS` 包含前端域名
- 检查协议是否匹配（http vs https）

### 部署失败
- 检查构建日志
- 确认依赖安装成功
- 验证环境变量配置

---

## 免费额度

- **Railway**: $5/月免费额度
- **Vercel**: 无限个人项目
- **Render**: 免费层可用（512MB RAM，有休眠限制）

对于个人项目，这些免费额度通常足够使用。

## 内存和性能分析

### 内存占用

根据代码分析，单局游戏的内存占用非常低：

- **游戏数据**：< 100KB（4 名玩家，每人 25 张牌）
- **Python 运行时**：60-100 MB
- **总内存占用**：约 60-100 MB

**结论**：512MB 完全足够，可支持 50-100 个并发房间。

### 逻辑复杂度

- **拖拉机检测**：O(n log n)，n ≤ 25，执行时间 < 1ms
- **甩牌验证**：O(n²)，n ≤ 25，执行时间 < 10ms
- **牌型比较**：O(n)，n ≤ 25，执行时间 < 1ms

**结论**：CPU 占用极低，0.1 CPU 完全足够。

详细分析请查看 `MEMORY_ANALYSIS.md`。

## 防止服务休眠

Render 免费实例会在 15 分钟无活动后休眠。可以使用以下方法保持服务活跃：

### 推荐方案：UptimeRobot

1. 访问 https://uptimerobot.com
2. 注册免费账号
3. 添加监控：
   - URL: `https://your-app.onrender.com/health`
   - 间隔: 5 分钟
4. 完成！服务将保持活跃

### 备选方案：GitHub Actions

项目已包含 `.github/workflows/keep-alive.yml`，可以自动每 10 分钟 ping 一次服务。

**启用步骤**：
1. 编辑 `.github/workflows/keep-alive.yml`
2. 将 `your-app.onrender.com` 替换为你的实际 URL
3. 提交代码，GitHub Actions 会自动运行

详细说明请查看 `KEEP_ALIVE.md`。

