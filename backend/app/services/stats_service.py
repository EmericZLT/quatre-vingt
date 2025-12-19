from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import Dict, List, Any
import logging

from app.models.user import User, Stats
from app.db.database import async_session

logger = logging.getLogger(__name__)

async def record_game_stats(round_summary: Dict[str, Any], players: List[Any]):
    """
    记录一局游戏的统计数据
    """
    async with async_session() as db:
        try:
            dealer_side = round_summary.get("dealer_side")
            dealer_level_up = round_summary.get("dealer_level_up", 0)
            idle_level_up = round_summary.get("idle_level_up", 0)
            dealer_wins = round_summary.get("dealer_wins", False)
            total_score = round_summary.get("total_score", 0)

            # 遍历所有玩家，如果是已注册用户（ID 为 UUID 格式），则更新其统计数据
            for player in players:
                # 简单判断是否为注册用户：ID 长度通常较长且包含横杠
                if not player.id or len(str(player.id)) < 20:
                    continue
                
                # 确定玩家属于哪一方
                is_dealer_side = False
                if dealer_side == "north_south":
                    is_dealer_side = player.position.value in ["north", "south"]
                else:
                    is_dealer_side = player.position.value in ["east", "west"]
                
                # 计算该玩家的升级数和胜负
                level_ups = dealer_level_up if is_dealer_side else idle_level_up
                win = 1 if (is_dealer_side and dealer_wins) or (not is_dealer_side and not dealer_wins) else 0
                
                # 更新数据库
                # 1. 更新 Stats 表
                stmt = select(Stats).where(Stats.user_id == player.id)
                result = await db.execute(stmt)
                stats = result.scalars().first()
                
                if stats:
                    stats.games_played += 1
                    stats.wins += win
                    if is_dealer_side:
                        stats.dealer_level_ups += level_ups
                    else:
                        stats.idle_level_ups += level_ups
                    stats.total_score += total_score
                
                # 记录日志以便调试
                logger.info(f"Updated stats for user {player.name} (ID: {player.id}): win={win}, level_ups={level_ups}")

            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to record game stats: {e}")
            await db.rollback()
            return False

