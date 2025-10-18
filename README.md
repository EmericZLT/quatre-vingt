# Quatre-Vingt 在线纸牌游戏

一个基于Web的实时纸牌游戏平台，让远方的朋友可以一起在线游戏。

## 技术栈

- **前端**: Vue.js + TypeScript
- **后端**: Python + FastAPI + WebSocket
- **数据库**: PostgreSQL + Redis
- **部署**: Vercel (前端) + Railway (后端)

## 项目结构

```
quatre-vingt/
├── frontend/          # Vue.js前端
├── backend/           # Python后端
├── assets/           # 游戏资源
└── docs/             # 文档
```

## 开发环境

- Python 3.12+
- Node.js 18+
- Conda环境: 80

## 快速开始

### 后端开发
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

## 部署

- 前端: 自动部署到 Vercel
- 后端: 自动部署到 Railway

## 贡献

欢迎提交Issue和Pull Request！
