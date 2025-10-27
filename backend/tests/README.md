# 测试文件说明

## 测试文件列表

### 基础组件测试
- `test_card_system.py` - 卡牌系统测试（创建、洗牌、发牌）
- `test_card_comparison.py` - 牌大小比较逻辑测试
- `test_tractor_logic.py` - 拖拉机识别逻辑测试
- `test_trump_logic.py` - 将吃逻辑测试

### 游戏流程测试
- `test_api.py` - API端点测试
- `test_game_state.py` - 游戏状态管理测试（发牌、底牌、庄家）
- `test_bidding_simple.py` - 亮主和反主系统测试

### 出牌系统测试
- `test_complete_card_playing.py` - 完整出牌流程测试
  - 单牌出牌
  - 对子出牌
  - 拖拉机出牌
  - 跟牌规则验证
  - 获胜者判断

- `test_slingshot.py` - 甩牌系统集成测试
  - 甩牌验证
  - 甩牌跟牌规则
  - 甩牌获胜者判断
  - 超将吃规则

- `test_slingshot_challenge.py` - 甩牌挑战逻辑测试
  - 挑战优先级（单牌 > 对子 > 拖拉机）
  - 强制出牌逻辑
  - 挑战者牌型灵活拆分

## 运行测试

在backend目录下运行：

```bash
# 运行所有测试
python -m pytest tests/

# 运行单个测试
python tests/test_slingshot.py

# 或使用python直接运行
E:\anaconda\anaconda\envs\80\python.exe tests/test_slingshot.py
```

## 测试覆盖范围

### 已完成
✅ 卡牌系统  
✅ 牌比较逻辑  
✅ 拖拉机识别  
✅ 将吃逻辑  
✅ 游戏状态管理  
✅ 亮主系统  
✅ 出牌系统（含甩牌）  

### 待实现
⏳ 计分系统  
⏳ WebSocket实时通信  
⏳ 完整游戏流程集成  

