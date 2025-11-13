import { defineStore } from 'pinia'

type Pos = 'NORTH'|'WEST'|'SOUTH'|'EAST'

export const useGameStore = defineStore('game', {
  state: () => ({
    roomId: '',
    phase: 'waiting' as 'waiting'|'dealing'|'bidding'|'playing'|'bottom',
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
    // 仅用于演示：每家展示用的"手里标签"列表（真实游戏中只对本家给出具体牌）
    demoHands: { NORTH: [] as string[], WEST: [] as string[], SOUTH: [] as string[], EAST: [] as string[] } as Record<Pos, string[]>,
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
      if (Array.isArray(s.my_hand_sorted)) {
        // 前端需知道自己位置；此处略过，仅占位
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
    applyPhaseChanged(e: { phase: 'waiting'|'dealing'|'bidding'|'playing'|'bottom' }) {
      this.phase = e.phase
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
    applyCardPlayed(e: { current_trick?: Array<{ player_id: string; player_position: string; cards?: string[]; card?: string }>; trick_complete?: boolean; current_player?: string }) {
      if (Array.isArray(e.current_trick)) {
        // 兼容旧的card字段，转换为cards数组
        this.current_trick = e.current_trick.map((item: any) => {
          if (item.cards) {
            return { ...item, cards: item.cards }
          } else if (item.card) {
            return { ...item, cards: [item.card] }
          }
          return item
        })
      }
      if (typeof e.current_player === 'string') {
        this.current_player = e.current_player
      }
      // 如果一轮完成，current_trick会被清空，但这里已经通过trick_complete事件处理
    },
    applyTrickComplete(e: { last_trick?: Array<{ player_id: string; player_position: string; cards?: string[]; card?: string }>; tricks_won?: { north_south: number; east_west: number }; current_player?: string; idle_score?: number }) {
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
      // 清空当前轮次
      this.current_trick = []
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
    }
  },
})


