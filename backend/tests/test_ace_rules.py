"""
测试打A相关规则
"""
import pytest
from app.models.game import GameRoom, Player, PlayerPosition, Card, Suit, Rank
from app.game.game_state import GameState


def create_test_room():
    """创建测试房间"""
    room = GameRoom(id="test_room", name="Test Room")
    room.players = [
        Player(id="p1", name="Player1", position=PlayerPosition.NORTH),
        Player(id="p2", name="Player2", position=PlayerPosition.EAST),
        Player(id="p3", name="Player3", position=PlayerPosition.SOUTH),
        Player(id="p4", name="Player4", position=PlayerPosition.WEST),
    ]
    return room


def test_75_score_no_upgrade():
    """测试需求1：75分庄家不升级"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 5
    gs.east_west_level = 3
    gs.game_phase = "playing"
    
    # 模拟闲家得75分
    gs.idle_score = 75
    
    # 调用游戏结束逻辑
    gs._handle_game_end()
    
    # 验证：庄家（南北方）不升级
    assert gs.north_south_level == 5, "75分时庄家不应升级"
    assert gs.round_summary["dealer_level_up"] == 0, "升级数应为0"


def test_70_score_upgrade():
    """测试70分庄家正常升级"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 5
    gs.east_west_level = 3
    gs.game_phase = "playing"
    
    # 模拟闲家得70分
    gs.idle_score = 70
    
    # 调用游戏结束逻辑
    gs._handle_game_end()
    
    # 验证：庄家（南北方）升1级
    assert gs.north_south_level == 6, "70分时庄家应升1级"
    assert gs.round_summary["dealer_level_up"] == 1, "升级数应为1"


def test_ace_win():
    """测试需求2：打A且升级时庄家胜利"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方），级别为A（14）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 14
    gs.east_west_level = 10
    gs.game_phase = "playing"
    
    # 模拟闲家得0分（庄家大胜）
    gs.idle_score = 0
    
    # 调用游戏结束逻辑
    gs._handle_game_end()
    
    # 验证：庄家胜利
    assert gs.round_summary["dealer_wins"] == True, "打A且升级应判定为胜利"
    assert gs.round_summary["dealer_level_up"] > 0, "应该有升级"


def test_ace_no_win():
    """测试打A但未升级时不胜利"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方），级别为A（14）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 14
    gs.east_west_level = 10
    gs.game_phase = "playing"
    
    # 模拟闲家得75分（庄家不升级）
    gs.idle_score = 75
    
    # 调用游戏结束逻辑
    gs._handle_game_end()
    
    # 验证：庄家未胜利
    assert gs.round_summary["dealer_wins"] == False, "打A但未升级不应判定为胜利"


def test_ace_count_penalty():
    """测试需求3：打A三次未胜利的惩罚"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方），级别为A（14）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 14
    gs.east_west_level = 10
    gs.game_phase = "playing"
    
    # 模拟第一次打A未胜利
    gs.north_south_ace_count = 2  # 已经打了2次
    gs.idle_score = 75  # 庄家不升级
    
    gs._handle_game_end()
    
    # 验证：第三次打A未胜利，级别被重置为2
    assert gs.north_south_level == 2, "第三次打A未胜利应重置为2"
    assert gs.north_south_ace_count == 0, "打A计数应清零"
    assert gs.round_summary["dealer_penalty"] == True, "应标记为惩罚"


def test_ace_count_increment():
    """测试打A次数正确累加"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方），级别为A（14）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 14
    gs.east_west_level = 10
    gs.game_phase = "playing"
    
    # 初始计数为0
    assert gs.north_south_ace_count == 0
    
    # 第一次打A未胜利
    gs.idle_score = 75
    gs._handle_game_end()
    
    assert gs.north_south_ace_count == 1, "第一次打A后计数应为1"
    
    # 模拟第二次打A未胜利
    gs.game_phase = "playing"
    gs.north_south_level = 14  # 仍然是A
    gs.idle_score = 75
    gs._handle_game_end()
    
    assert gs.north_south_ace_count == 2, "第二次打A后计数应为2"


def test_ace_count_reset_on_win():
    """测试胜利后打A计数清零"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方），级别为A（14）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 14
    gs.east_west_level = 10
    gs.game_phase = "playing"
    
    # 模拟已经打了2次A
    gs.north_south_ace_count = 2
    
    # 这次胜利
    gs.idle_score = 0
    gs._handle_game_end()
    
    # 验证：胜利后计数清零
    assert gs.north_south_ace_count == 0, "胜利后打A计数应清零"
    assert gs.round_summary["dealer_wins"] == True


def test_game_reset_after_win():
    """测试胜利后游戏重置"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为NORTH（南北方），级别为A（14）
    gs.dealer_position = PlayerPosition.NORTH
    gs.north_south_level = 14
    gs.east_west_level = 10
    gs.game_phase = "playing"
    gs.is_first_round = False
    
    # 模拟胜利
    gs.idle_score = 0
    gs._handle_game_end()
    
    # 进入scoring阶段
    assert gs.game_phase == "scoring"
    assert gs.round_summary["dealer_wins"] == True
    assert gs.round_summary["winner_side"] == "north_south", "应记录胜利方"
    assert gs.round_summary["winner_side_name"] == "南北方", "应记录胜利方名称"
    
    # 模拟所有玩家准备
    for player in room.players:
        gs.players_ready_for_next_round.add(player.id)
    
    # 开始下一轮
    success = gs.start_next_round()
    
    # 验证：游戏重置
    assert success == True
    assert gs.north_south_level == 2, "级别应重置为2"
    assert gs.east_west_level == 2, "级别应重置为2"
    assert gs.is_first_round == True, "应标记为第一局"
    assert gs.fixed_dealer_position in [PlayerPosition.NORTH, PlayerPosition.SOUTH], "南北方胜利应成为定主方"


def test_winner_info_in_summary():
    """测试胜利信息正确记录在round_summary中"""
    room = create_test_room()
    gs = GameState(room)
    
    # 设置庄家为EAST（东西方），级别为A（14）
    gs.dealer_position = PlayerPosition.EAST
    gs.north_south_level = 10
    gs.east_west_level = 14
    gs.game_phase = "playing"
    
    # 模拟胜利
    gs.idle_score = 0
    gs._handle_game_end()
    
    # 验证胜利信息
    assert gs.round_summary["dealer_wins"] == True, "应标记为胜利"
    assert gs.round_summary["winner_side"] == "east_west", "胜利方应为东西方"
    assert gs.round_summary["winner_side_name"] == "东西方", "胜利方名称应为东西方"
    
    # 测试未胜利的情况
    gs2 = GameState(create_test_room())
    gs2.dealer_position = PlayerPosition.NORTH
    gs2.north_south_level = 14
    gs2.game_phase = "playing"
    gs2.idle_score = 75  # 不升级
    gs2._handle_game_end()
    
    assert gs2.round_summary["dealer_wins"] == False, "应标记为未胜利"
    assert gs2.round_summary["winner_side"] is None, "未胜利时winner_side应为None"
    assert gs2.round_summary["winner_side_name"] is None, "未胜利时winner_side_name应为None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

