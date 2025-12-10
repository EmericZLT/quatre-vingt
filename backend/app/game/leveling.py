"""
升级规则模块
支持多种升级速度的规则
"""
from typing import Dict, Tuple


def calculate_level_up_default(
    final_idle_score: int,
    dealer_level: int  # pylint: disable=unused-argument
) -> Tuple[int, int, int]:
    """
    默认升级规则（当前使用的规则）
    
    规则：
    1. 分数抹零（向下取整到10的倍数，75分特殊处理）
    2. 如果得分 <= 0，庄家方升12级（特殊逻辑）
    3. 如果 >= 80，闲家升级 (score - 80) // 10
    4. 如果 < 80，庄家升级 (80 - score) // 10，但75分时庄家不升级
    
    Args:
        final_idle_score: 闲家最终得分（包括扣底）
        dealer_level: 庄家当前级别
        
    Returns:
        Tuple[dealer_level_up, idle_level_up, rounded_score]
        - dealer_level_up: 庄家升级级数
        - idle_level_up: 闲家升级级数
        - rounded_score: 抹零后的分数（用于计算）
    """
    # 特殊逻辑：如果得分 <= 0，庄家方升12级
    if final_idle_score <= 0:
        dealer_level_up = 12
        idle_level_up = 0
        rounded_score = final_idle_score  # 如实赋值，保持原值（可能是负数）
        return dealer_level_up, idle_level_up, rounded_score
    
    # 分数抹零（向下取整到10的倍数，仅用于计算升级）
    # 特殊处理75分，不抹零为70分，而是直接视为75分（庄家不升级）
    if final_idle_score == 75:
        rounded_score = 75
    else:
        rounded_score = (final_idle_score // 10) * 10
    
    # 计算升级
    if rounded_score >= 80:
        # 闲家升级
        idle_level_up = (rounded_score - 80) // 10
        dealer_level_up = 0
    else:
        # 庄家升级
        # 75分时庄家不升级
        if rounded_score == 75:
            dealer_level_up = 0
        else:
            dealer_level_up = (80 - rounded_score) // 10
        idle_level_up = 0
    
    return dealer_level_up, idle_level_up, rounded_score


def calculate_level_up_standard(
    final_idle_score: int,
    dealer_level: int  # pylint: disable=unused-argument
) -> Tuple[int, int, int]:
    """
    标准升级规则
    
    规则：
    1. 如果得分 <= 0，庄家方升 3 + abs(score) // 40 级（0分升3级，每少40分多升1级）
    2. 如果得分 > 0 且 < 40，庄家连升 2 级
    3. 如果得分 >= 40 且 < 80，庄家方升 1 级
    4. 如果得分 >= 80，抓分方升 (score - 80) // 40 级
    
    Args:
        final_idle_score: 闲家最终得分（包括扣底）
        dealer_level: 庄家当前级别
        
    Returns:
        Tuple[dealer_level_up, idle_level_up, rounded_score]
        - dealer_level_up: 庄家升级级数
        - idle_level_up: 闲家升级级数
        - rounded_score: 原始分数（用于计算，不抹零）
    """
    rounded_score = final_idle_score  # 标准规则不抹零，使用原始分数
    
    if final_idle_score < 80:
        # 得分 < 80，庄家升级：每40分升一级，统一公式 (80-score)//40+1，40分特殊处理
        dealer_level_up = (80 - final_idle_score) // 40 + 1 - (1 if final_idle_score == 40 else 0)
        idle_level_up = 0
    else:
        # 得分 >= 80，抓分方升 (score - 80) // 40 级
        dealer_level_up = 0
        idle_level_up = (final_idle_score - 80) // 40
    
    return dealer_level_up, idle_level_up, rounded_score


# 升级函数映射表
LEVEL_UP_FUNCTIONS: Dict[str, callable] = {
    "default": calculate_level_up_default,
    "standard": calculate_level_up_standard,
}


def get_level_up_function(level_up_mode: str = "default") -> callable:
    """
    根据模式获取对应的升级函数
    
    Args:
        level_up_mode: 升级模式，可选值："default", "standard"
        
    Returns:
        升级函数
        
    Raises:
        ValueError: 如果模式不存在
    """
    if level_up_mode not in LEVEL_UP_FUNCTIONS:
        raise ValueError(f"未知的升级模式: {level_up_mode}，可选值: {list(LEVEL_UP_FUNCTIONS.keys())}")
    return LEVEL_UP_FUNCTIONS[level_up_mode]


def calculate_level_up(
    final_idle_score: int,
    dealer_level: int,
    level_up_mode: str = "default"
) -> Tuple[int, int, int]:
    """
    计算升级级数（统一入口）
    
    Args:
        final_idle_score: 闲家最终得分（包括扣底）
        dealer_level: 庄家当前级别
        level_up_mode: 升级模式，可选值："default", "standard"
        
    Returns:
        Tuple[dealer_level_up, idle_level_up, rounded_score]
        - dealer_level_up: 庄家升级级数
        - idle_level_up: 闲家升级级数
        - rounded_score: 抹零后的分数（用于计算，standard模式返回原始分数）
    """
    level_up_func = get_level_up_function(level_up_mode)
    return level_up_func(final_idle_score, dealer_level)

