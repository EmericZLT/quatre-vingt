# 快速部署指南

## 🚀 一键部署到互联网

### 方案：Railway (后端) + Vercel (前端)

---

## 📋 部署步骤

### 第一步：准备 GitHub 仓库

1. 确保代码已推送到 GitHub
2. 确保 `backend/requirements.txt` 存在且包含所有依赖

### 第二步：部署后端到 Railway

1. **访问 Railway**
   - 打开 https://railway.app
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库

3. **配置服务**
   - Railway 会自动检测到 Python 项目
   - 如果没有自动检测，在设置中：
     - Root Directory: `backend`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **设置环境变量**
   在 Railway 项目设置 → Variables 中添加：
   ```
   ALLOWED_ORIGINS=["https://your-app.vercel.app"]
   PORT=8000
   DEBUG=False
   SECRET_KEY=生成一个随机字符串
   ```

5. **获取后端 URL**
   - Railway 会提供一个域名，例如：`your-app.up.railway.app`
   - 记下这个 URL（后续需要）

### 第三步：部署前端到 Vercel

1. **访问 Vercel**
   - 打开 https://vercel.com
   - 使用 GitHub 账号登录

2. **导入项目**
   - 点击 "Add New Project"
   - 选择你的 GitHub 仓库
   - Framework Preset: **Vite**

3. **配置项目**
   - Root Directory: `frontend`
   - Build Command: `npm run build`（自动检测）
   - Output Directory: `dist`（自动检测）

4. **设置环境变量**
   在项目设置 → Environment Variables 中添加：
   ```
   VITE_API_URL=https://your-app.up.railway.app
   VITE_WS_URL=wss://your-app.up.railway.app
   ```
   ⚠️ **注意**：使用 `wss://`（WebSocket Secure），不是 `ws://`

5. **部署**
   - 点击 "Deploy"
   - 等待构建完成
   - 获取前端 URL，例如：`your-app.vercel.app`

### 第四步：更新后端 CORS 配置

回到 Railway，更新环境变量：
```
ALLOWED_ORIGINS=["https://your-app.vercel.app"]
```

Railway 会自动重新部署。

---

## ✅ 完成！

现在访问你的 Vercel URL，游戏应该可以正常工作了！

---

## 🔧 故障排查

### WebSocket 连接失败
- ✅ 检查 `VITE_WS_URL` 是否使用 `wss://`（不是 `ws://`）
- ✅ 检查后端 URL 是否正确
- ✅ 查看浏览器控制台的错误信息

### CORS 错误
- ✅ 确保 `ALLOWED_ORIGINS` 包含你的前端域名（带 `https://`）
- ✅ 确保协议匹配（都是 https）

### 前端无法连接后端
- ✅ 检查 `VITE_API_URL` 是否正确
- ✅ 检查后端是否正常运行（访问 `https://your-backend.railway.app/health`）

---

## 💡 提示

1. **自定义域名**：Railway 和 Vercel 都支持绑定自己的域名
2. **环境变量**：生产环境不要使用默认的 `SECRET_KEY`
3. **监控**：两个平台都提供日志和监控功能

---

## 📚 其他部署选项

如果不想用 Railway，也可以使用：
- **Render** (https://render.com) - 类似 Railway
- **Fly.io** (https://fly.io) - 支持全球部署
- **Heroku** (https://heroku.com) - 需要付费

前端也可以部署到：
- **Netlify** (https://netlify.com) - 类似 Vercel

---

## 🎉 享受你的在线游戏！

部署完成后，你可以：
- 分享链接给朋友
- 在任何设备上访问
- 实时多人游戏

