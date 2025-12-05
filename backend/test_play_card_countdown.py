import asyncio
import json
import websockets
import random
import string

async def test_play_card_countdown():
    """测试玩家出牌后倒计时是否会为下一个玩家重启"""
    print("测试玩家出牌后倒计时重启功能...")
    
    # 创建房间
    room_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # 玩家连接
    players = []
    websockets_list = []
    
    try:
        # 创建4个玩家连接
        for i in range(4):
            player_id = f'p{i+1}'
            player_name = f'Player {i+1}'
            ws_url = f"ws://localhost:8000/ws/game/{room_id}?player_id={player_id}"
            
            ws = await websockets.connect(ws_url)
            websockets_list.append(ws)
            
            # 接收初始消息
            asyncio.create_task(receive_messages(ws, player_name))
            
            players.append({
                "id": player_id,
                "name": player_name,
                "ws": ws
            })
        
        print("4个玩家已连接")
        await asyncio.sleep(2)  # 等待游戏初始化
        
        # 开始游戏
        await players[0]["ws"].send(json.dumps({"type": "start_game"}))
        print("游戏已开始")
        await asyncio.sleep(2)  # 等待游戏开始
        
        # 等待第一轮玩家1的倒计时开始
        print("等待玩家1的倒计时开始...")
        await asyncio.sleep(3)
        
        # 玩家1出牌
        print("玩家1准备出牌...")
        await players[0]["ws"].send(json.dumps({
            "type": "play_card",
            "cards": "S2"
        }))
        
        # 等待出牌处理和倒计时重启
        await asyncio.sleep(5)
        
        print("测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        # 关闭所有连接
        for ws in websockets_list:
            await ws.close()
        
async def receive_messages(ws, player_name):
    """接收并打印来自服务器的消息"""
    try:
        while True:
            message = await ws.recv()
            data = json.loads(message)
            
            # 只打印关键消息
            if data["type"] in ["game_state", "countdown_updated", "card_played", "error"]:
                if data["type"] == "countdown_updated":
                    print(f"[{player_name}] 倒计时更新: current_countdown={data.get('current_countdown')}, countdown_active={data.get('countdown_active')}")
                elif data["type"] == "card_played":
                    print(f"[{player_name}] 玩家 {data.get('player_id')} 出牌: {data.get('cards')}")
                elif data["type"] == "error":
                    print(f"[{player_name}] 错误: {data.get('message')}")
    except websockets.ConnectionClosed:
        print(f"[{player_name}] 连接已关闭")
    except Exception as e:
        print(f"[{player_name}] 接收消息时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_play_card_countdown())