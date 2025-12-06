import { defineStore } from 'pinia'

type Pos = 'NORTH'|'WEST'|'SOUTH'|'EAST'

export const useGameStore = defineStore('game', {
  state: () => ({
    roomId: '',
    phase: 'waiting' as 'waiting'|'dealing'|'bidding'|'playing'|'bottom'|'scoring',
    dealer_position: 'NORTH' as Pos,
    dealer_player_id: '',
    dealer_has_bottom: false,
    bottom_pending: false,
    trump_suit: null as null | '♠'|'♥'|'♣'|'♦',
    dealt_count: 0,
    players: [] as Array<{ id: string; name?: string; position: Pos; cards_count: number }> ,
    bottom_cards_count: 0,
    idle_score: 0,  // 闲家得分（庄家不计分）
    tricks_won: { north_south: 0, east_west: 0 },
    bottom_cards: [] as string[],
    current_trick: [] as Array<{ player_id: string; player_position: string; cards: string[] }>,
    last_trick: [] as Array<{ player_id: string; player_position: string; cards: string[] }>,
    current_player: null as string | null,  // 当前应该出牌的玩家位置
    waitingForNextTrick: false,  // 标志：一轮刚结束，等待新一轮开始（用于保留上一轮的牌显示）
    // 倒计时相关状态
    countdown: 24,  // 当前倒计时秒数
    countdownActive: false,  // 倒计时是否激活
    // 仅用于演示：每家展示用的"手里标签"列表（真实游戏中只对本家给出具体牌）
    demoHands: { NORTH: [] as string[], WEST: [] as string[], SOUTH: [] as string[], EAST: [] as string[] } as Record<Pos, string[]>,
    // 本局游戏总结信息
    round_summary: null as null | {
      idle_score: number
      bottom_score: number
      bottom_bonus: number
      total_score: number  // 完整分数，不抹零
      dealer_side: string  // "north_south" 或 "east_west"
      idle_side: string
      dealer_level_up: number
      idle_level_up: number
      old_north_south_level: number
      old_east_west_level: number
      new_north_south_level: number
      new_east_west_level: number
      next_dealer: string
      next_dealer_name: string
      bottom_cards?: string[]  // 本局底牌（用于查看）
      tricks_won: { north_south: number; east_west: number }
      dealer_wins?: boolean  // 庄家是否胜利（打A且升级）
      winner_side?: string | null  // 胜利方："north_south" 或 "east_west"，无胜利时为null
      winner_side_name?: string | null  // 胜利方名称："南北方" 或 "东西方"，无胜利时为null
      dealer_penalty?: boolean  // 庄家是否被惩罚（打A三次未胜利）
      north_south_ace_count?: number  // 南北方打A次数
      east_west_ace_count?: number  // 东西方打A次数
    },
    // 准备下一轮的玩家状态
    ready_for_next_round: {
      ready_count: 0,
      total_players: 0,
      ready_players: [] as string[]
    },
    // 准备开始游戏的玩家状态（waiting阶段）
    ready_to_start: {
      ready_count: 0,
      total_players: 0,
      ready_players: [] as string[]
    },
    // 自动出牌类型
    auto_play_type: null as 'selected_cards' | 'auto_logic' | null,
  }),
  actions: {
    applySnapshot(s: any) {
      this.roomId = s.room_id || this.roomId
      this.phase = s.phase || this.phase
      this.dealer_position = (s.dealer_position as Pos) || this.dealer_position
      this.dealer_player_id = s.dealer_player_id || this.dealer_player_id
      this.dealer_has_bottom = !!s.dealer_has_bottom
      this.bottom_pending = !!s.bottom_pending
      this.trump_suit = (s.trump_suit as any) ?? this.trump_suit
      this.dealt_count = s.dealt_count ?? this.dealt_count
      this.players = (s.players || []).map((p: any) => ({ id: p.id, name: p.name, position: p.position, cards_count: p.cards_count }))
      this.bottom_cards_count = s.bottom_cards_count ?? this.bottom_cards_count
      if (typeof s.idle_score === 'number') this.idle_score = s.idle_score
      this.tricks_won = s.tricks_won || this.tricks_won
      if (Array.isArray(s.bottom_cards)) {
        this.bottom_cards = s.bottom_cards
      }
      if (Array.isArray(s.current_trick)) {
        // 如果一轮刚结束（waitingForNextTrick为true）且后端发送空的current_trick，不要清空前端的牌
        // 这样可以让玩家看到上一轮的4张牌，直到新一轮第一名玩家出牌
        if (this.waitingForNextTrick && s.current_trick.length === 0) {
          // 保持current_trick不变，不清空
          console.log('[GameStore] applySnapshot: 保留上一轮的牌显示，等待新一轮开始')
        } else {
          // 兼容旧的card字段，转换为cards数组
          this.current_trick = s.current_trick.map((item: any) => {
            if (item.cards) {
              return { ...item, cards: item.cards }
            } else if (item.card) {
              return { ...item, cards: [item.card] }
            }
            return item
          })
        }
      }
      if (Array.isArray(s.last_trick)) {
        // 兼容旧的card字段，转换为cards数组
        this.last_trick = s.last_trick.map((item: any) => {
          if (item.cards) {
            return { ...item, cards: item.cards }
          } else if (item.card) {
            return { ...item, cards: [item.card] }
          }
          return item
        })
      }
      if (typeof s.current_player === 'string') {
        this.current_player = s.current_player
      }
      // 处理倒计时相关信息
      if (typeof s.countdown === 'number') {
        this.countdown = s.countdown
      }
      if (typeof s.countdown_active === 'boolean') {
        this.countdownActive = s.countdown_active
      }
      if (Array.isArray(s.my_hand_sorted)) {
        // 前端需知道自己位置；此处略过，仅占位
      }
      // 处理本局总结信息
      if (s.round_summary) {
        this.round_summary = s.round_summary
      }
      // 处理准备下一轮的状态
      if (s.ready_for_next_round) {
        this.ready_for_next_round = {
          ready_count: s.ready_for_next_round.ready_count || 0,
          total_players: s.ready_for_next_round.total_players || 0,
          ready_players: s.ready_for_next_round.ready_players || []
        }
      }
      // 处理准备开始游戏的状态
      if (s.ready_to_start) {
        this.ready_to_start = {
          ready_count: s.ready_to_start.ready_count || 0,
          total_players: s.ready_to_start.total_players || 0,
          ready_players: s.ready_to_start.ready_players || []
        }
      }
    },
    applyBottomUpdate(e: { bottom_cards_count?: number; dealer_has_bottom?: boolean; bottom_pending?: boolean; dealer_player_id?: string }) {
      if (typeof e.bottom_cards_count === 'number') this.bottom_cards_count = e.bottom_cards_count
      if (typeof e.dealer_has_bottom === 'boolean') this.dealer_has_bottom = e.dealer_has_bottom
      if (typeof e.bottom_pending === 'boolean') this.bottom_pending = e.bottom_pending
      if (typeof e.dealer_player_id === 'string') this.dealer_player_id = e.dealer_player_id
    },
    applySnapshotBottomCards(cards: string[] | undefined) {
      if (Array.isArray(cards)) this.bottom_cards = cards
    },
    applyDealTick(e: { player: string; card: string; dealt_count?: number }) {
      // 将后端返回的小写 player 转换为大写（如 "north" -> "NORTH"）
      const player = (e.player?.toUpperCase() as Pos) || null
      const { card } = e
      console.log('[GameStore] applyDealTick:', { player, card, originalPlayer: e.player, dealt_count: e.dealt_count })
      if (player && card && player in this.demoHands) {
        this.demoHands[player] = [...this.demoHands[player], card]
        console.log('[GameStore] Updated hand for', player, ':', this.demoHands[player].length, 'cards')
      } else {
        console.warn('[GameStore] Failed to update hand:', { player, card, validPlayer: player && player in this.demoHands })
      }
      if (typeof e.dealt_count === 'number') this.dealt_count = e.dealt_count
      else this.dealt_count += 1
      // 同步 players 的 cards_count（若需要）
      const p = this.players.find(x => x.position === player)
      if (p) p.cards_count += 1
    },
    applyPhaseChanged(e: { phase: 'waiting'|'dealing'|'bidding'|'playing'|'bottom'|'scoring' }) {
      this.phase = e.phase
      // 进入新阶段时，重置waitingForNextTrick标志
      if (e.phase === 'dealing' || e.phase === 'waiting') {
        this.waitingForNextTrick = false
        console.log('[GameStore] applyPhaseChanged: 重置waitingForNextTrick=false')
      }
    },
    applyScoreUpdated(e: { idle_score?: number }) {
      if (typeof e.idle_score === 'number') this.idle_score = e.idle_score
    },
    applyKoudiApplied(e: { bottom_score: number; multiplier: number; bonus: number }) {
      // 前端只展示；状态不强行改分，由后端随后推 score_updated
    },
    applyPlayCard(e: { player: Pos; cards: string[] }) {
      // 动画事件：可用于当前墩展示；此处演示不做本地状态
    },
    applyTrickWon(e: { winner: Pos; trick_points?: number }) {
      if (!e.winner) return
      if (e.winner === 'NORTH' || e.winner === 'SOUTH') this.tricks_won.north_south += 1
      else this.tricks_won.east_west += 1
    },
    applyCardPlayed(e: { current_trick?: Array<{ player_id: string; player_position: string; cards?: string[]; card?: string; slingshot_failed?: boolean }>; trick_complete?: boolean; current_player?: string; slingshot_failed?: boolean; play_type?: 'selected_cards' | 'auto_logic' }) {
      // 如果一轮完成（trick_complete为true），保留current_trick，不清空，等待新一轮开始
      if (e.trick_complete) {
        // 一轮完成，保留current_trick中的4张牌，不清空
        // 设置标志，表示一轮刚结束，等待新一轮开始
        this.waitingForNextTrick = true
        console.log('[GameStore] applyCardPlayed: 一轮完成，设置waitingForNextTrick=true')
        
        if (Array.isArray(e.current_trick) && e.current_trick.length > 0) {
          // 更新current_trick为包含4张牌的数据（第四名玩家刚出的牌）
          this.current_trick = e.current_trick.map((item: any) => {
            const mapped: any = {}
            if (item.cards) {
              mapped.cards = item.cards
            } else if (item.card) {
              mapped.cards = [item.card]
            }
            return { ...item, ...mapped }
          })
          console.log('[GameStore] applyCardPlayed: 更新current_trick为4张牌')
        } else {
          // 如果current_trick为空或未定义，保持当前的current_trick不变（不清空）
          // 这样可以让上一轮的牌继续显示，直到新一轮开始
          console.log('[GameStore] applyCardPlayed: 保持current_trick不变')
        }
      } else if (Array.isArray(e.current_trick)) {
        // 如果是新的一轮开始（领出，current_trick.length === 1），先清空上一轮的牌
        if (e.current_trick.length === 1 && !e.slingshot_failed) {
          // 新的一轮开始，清空上一轮的牌，并清除标志
          console.log('[GameStore] applyCardPlayed: 新一轮开始，清空上一轮的牌，设置waitingForNextTrick=false')
          this.current_trick = []
          this.waitingForNextTrick = false
        }
        // 兼容旧的card字段，转换为cards数组
        this.current_trick = e.current_trick.map((item: any) => {
          const mapped: any = {}
          if (item.cards) {
            mapped.cards = item.cards
          } else if (item.card) {
            mapped.cards = [item.card]
          }
          // 保留其他字段，包括slingshot_failed标记
          return { ...item, ...mapped }
        })
        console.log('[GameStore] applyCardPlayed: 更新current_trick，长度=', this.current_trick.length)
      }
      if (typeof e.current_player === 'string') {
        this.current_player = e.current_player
      }
      // 设置自动出牌类型（如果存在）
      if (e.play_type === 'selected_cards' || e.play_type === 'auto_logic') {
        console.log('[GameStore] applyCardPlayed: 设置auto_play_type为', e.play_type)
        this.auto_play_type = e.play_type
      }
    },
    applyTrickComplete(e: { last_trick?: Array<{ player_id: string; player_position: string; cards?: string[]; card?: string }>; current_trick?: Array<{ player_id: string; player_position: string; cards?: string[]; card?: string }>; tricks_won?: { north_south: number; east_west: number }; current_player?: string; idle_score?: number }) {
      // 一轮完成，设置标志
      this.waitingForNextTrick = true
      console.log('[GameStore] applyTrickComplete: 设置waitingForNextTrick=true')
      
      if (Array.isArray(e.last_trick)) {
        // 兼容旧的card字段，转换为cards数组
        this.last_trick = e.last_trick.map((item: any) => {
          if (item.cards) {
            return { ...item, cards: item.cards }
          } else if (item.card) {
            return { ...item, cards: [item.card] }
          }
          return item
        })
      }
      // 如果提供了current_trick，更新它（用于延迟显示）
      // 注意：不清空current_trick，保留上一轮的4张牌，等待新一轮第一名玩家出牌时再清空
      if (Array.isArray(e.current_trick) && e.current_trick.length > 0) {
        // 兼容旧的card字段，转换为cards数组
        // 更新current_trick为last_trick的副本（包含4张牌）
        this.current_trick = e.current_trick.map((item: any) => {
          if (item.cards) {
            return { ...item, cards: item.cards }
          } else if (item.card) {
            return { ...item, cards: [item.card] }
          }
          return item
        })
        console.log('[GameStore] applyTrickComplete: 更新current_trick，长度=', this.current_trick.length)
      } else {
        console.log('[GameStore] applyTrickComplete: 保持current_trick不变')
      }
      // 如果没有提供current_trick或current_trick为空，保持当前值不变（不清空，保留上一轮的牌）
      if (e.tricks_won) {
        this.tricks_won = e.tricks_won
      }
      if (typeof e.idle_score === 'number') {
        this.idle_score = e.idle_score
      }
      if (typeof e.current_player === 'string') {
        this.current_player = e.current_player
      }
    },
    resetDemoHands() {
      this.demoHands = { NORTH: [], WEST: [], SOUTH: [], EAST: [] }
      this.dealt_count = 0
    },
    applyRoundEnd(e: { round_summary?: any; ready_count?: number; total_players?: number; ready_players?: string[] }) {
      if (e.round_summary) {
        this.round_summary = e.round_summary
      }
      if (typeof e.ready_count === 'number') {
        this.ready_for_next_round.ready_count = e.ready_count
      }
      if (typeof e.total_players === 'number') {
        this.ready_for_next_round.total_players = e.total_players
      }
      if (Array.isArray(e.ready_players)) {
        this.ready_for_next_round.ready_players = e.ready_players
      }
    },
    applyReadyForNextRoundUpdated(e: { player_id?: string; ready_count?: number; total_players?: number; all_ready?: boolean; ready_players?: string[] }) {
      if (typeof e.ready_count === 'number') {
        this.ready_for_next_round.ready_count = e.ready_count
      }
      if (typeof e.total_players === 'number') {
        this.ready_for_next_round.total_players = e.total_players
      }
      if (Array.isArray(e.ready_players)) {
        // 更新ready_players列表（完整列表）
        this.ready_for_next_round.ready_players = e.ready_players
      } else if (e.player_id) {
        // 如果没有提供ready_players列表，但有player_id，则添加到列表中
        if (!this.ready_for_next_round.ready_players.includes(e.player_id)) {
          this.ready_for_next_round.ready_players.push(e.player_id)
        }
      }
    },
    applyReadyToStartUpdated(e: { player_id?: string; ready_count?: number; total_players?: number; all_ready?: boolean; ready_players?: string[] }) {
      if (typeof e.ready_count === 'number') {
        this.ready_to_start.ready_count = e.ready_count
      }
      if (typeof e.total_players === 'number') {
        this.ready_to_start.total_players = e.total_players
      }
      if (Array.isArray(e.ready_players)) {
        // 更新ready_players列表（完整列表）
        this.ready_to_start.ready_players = e.ready_players
      } else if (e.player_id) {
        // 如果没有提供ready_players列表，但有player_id，则添加到列表中
        if (!this.ready_to_start.ready_players.includes(e.player_id)) {
          this.ready_to_start.ready_players.push(e.player_id)
        }
      }
    },
    applyPlayersUpdated(e: { players?: any[]; ready_to_start?: { ready_count?: number; total_players?: number; ready_players?: string[] } }) {
      // 更新玩家列表
      if (Array.isArray(e.players)) {
        this.players = e.players.map((p: any) => ({ 
          id: p.id, 
          name: p.name, 
          position: p.position, 
          cards_count: p.cards_count 
        }))
      }
      // 更新准备状态（如果在waiting阶段）
      if (e.ready_to_start && this.phase === 'waiting') {
        if (typeof e.ready_to_start.ready_count === 'number') {
          this.ready_to_start.ready_count = e.ready_to_start.ready_count
        }
        if (typeof e.ready_to_start.total_players === 'number') {
          this.ready_to_start.total_players = e.ready_to_start.total_players
        }
        if (Array.isArray(e.ready_to_start.ready_players)) {
          this.ready_to_start.ready_players = e.ready_to_start.ready_players
        }
      }
    },
    applyCountdownUpdated(e: { countdown?: number; countdown_active?: boolean }) {
      if (typeof e.countdown === 'number') {
        this.countdown = e.countdown
      }
      if (typeof e.countdown_active === 'boolean') {
        this.countdownActive = e.countdown_active
      }
    },
    applyAutoPlay(e: { success: boolean; message?: string; played_cards?: string[]; current_trick?: Array<{ player_id: string; player_position: string; cards?: string[]; card?: string; slingshot_failed?: boolean }>; trick_complete?: boolean; current_player?: string; play_type?: 'selected_cards' | 'auto_logic' }) {
      // 处理auto_play消息
      console.log('[GameStore] applyAutoPlay:', e)
      
      // 保存自动出牌类型
      if (e.play_type === 'selected_cards' || e.play_type === 'auto_logic') {
        this.auto_play_type = e.play_type
      } else {
        this.auto_play_type = null
      }
      
      // 如果有current_trick，更新当前轮次的牌
      if (Array.isArray(e.current_trick)) {
        // 兼容旧的card字段，转换为cards数组
        this.current_trick = e.current_trick.map((item: any) => {
          const mapped: any = {};
          if (item.cards) {
            mapped.cards = item.cards;
          } else if (item.card) {
            mapped.cards = [item.card];
          }
          // 保留其他字段，包括slingshot_failed标记
          return { ...item, ...mapped };
        });
        
        // 如果是新的一轮开始（领出，current_trick.length === 1），先清空上一轮的牌
        if (e.current_trick.length === 1) {
          this.waitingForNextTrick = false;
        }
      }
      
      // 如果一轮完成，设置标志
      if (e.trick_complete) {
        this.waitingForNextTrick = true;
      }
      
      // 更新当前玩家
      if (typeof e.current_player === 'string') {
        this.current_player = e.current_player;
      }
    }
  },
})

