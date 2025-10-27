# 更新日志

## 2025-10-27 - 测试文件整理

### 整理内容
- 创建 `tests/` 目录统一管理所有测试文件
- 移动11个核心测试文件到 `tests/` 目录
- 删除7个过时的甩牌测试文件
- 删除2个临时说明文档

### 保留的测试文件（共11个）

#### 基础组件测试（4个）
- `test_card_system.py` - 卡牌系统
- `test_card_comparison.py` - 牌比较逻辑
- `test_tractor_logic.py` - 拖拉机识别
- `test_trump_logic.py` - 将吃逻辑

#### 游戏流程测试（3个）
- `test_api.py` - API端点
- `test_game_state.py` - 游戏状态管理
- `test_bidding_simple.py` - 亮主系统

#### 出牌系统测试（3个）
- `test_complete_card_playing.py` - 完整出牌流程
- `test_slingshot.py` - 甩牌系统集成（784行）
- `test_slingshot_challenge.py` - 甩牌挑战逻辑（327行）

#### 文档（1个）
- `README.md` - 测试说明文档

### 删除的文件（共9个）

#### 过时测试（7个）
- `test_slingshot_new.py`
- `test_slingshot_instant_validation.py`
- `test_slingshot_challenge_correct.py`
- `test_slingshot_challenge_rules.py`
- `test_slingshot_forced_cards.py`
- `test_forced_cards_correct.py`
- `test_slingshot_final.py` (已重命名为 `test_slingshot_challenge.py`)

#### 临时文档（2个）
- `TESTS_CLEANUP_PLAN.md`
- `SLINGSHOT_LOGIC_EXPLANATION.md`

### 项目结构
```
backend/
├── app/                    # 应用代码
│   ├── api/               # REST API
│   ├── core/              # 核心配置
│   ├── game/              # 游戏逻辑
│   ├── models/            # 数据模型
│   ├── services/          # 服务层
│   └── websocket/         # WebSocket
├── tests/                 # 测试文件
│   ├── README.md
│   ├── test_*.py (11个测试文件)
├── main.py                # 应用入口
├── requirements.txt       # 依赖列表
└── env.example            # 环境变量示例
```

## 2025-10-27 - 甩牌系统完成

### 实现功能
✅ 甩牌验证逻辑
✅ 甩牌挑战检测（即时验证）
✅ 甩牌优先级（单牌 > 对子 > 拖拉机）
✅ 强制出牌逻辑
✅ 挑战者牌型灵活拆分
✅ 甩牌跟牌规则
✅ 甩牌超将吃规则

### 核心实现
- `app/game/slingshot_logic.py` - 甩牌核心逻辑
- `app/game/card_playing.py` - 出牌系统集成

## 已完成功能

✅ 卡牌系统（创建、洗牌、发牌）
✅ 牌大小比较（动态级牌、主副牌）
✅ 拖拉机识别（动态相邻关系）
✅ 将吃和超将吃逻辑
✅ 游戏状态管理（发牌、底牌、庄家）
✅ 亮主和反主系统
✅ 完整出牌系统（单牌、对子、拖拉机、甩牌）

## 待实现功能

⏳ 计分系统
⏳ WebSocket实时通信
⏳ 前端界面
⏳ 部署配置

