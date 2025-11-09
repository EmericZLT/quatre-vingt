import { defineStore } from 'pinia'

type Pos = 'NORTH'|'WEST'|'SOUTH'|'EAST'

export const useGameStore = defineStore('game', {
  state: () => ({
    roomId: '',
    phase: 'waiting' as 'waiting'|'dealing'|'bidding'|'playing',
    dealer_position: 'NORTH' as Pos,
    trump_suit: null as null | '♠'|'♥'|'♣'|'♦',
    dealt_count: 0,
    players: [] as Array<{ id: string; name?: string; position: Pos; cards_count: number }>,
    bottom_cards_count: 0,
    scores: { north_south: 0, east_west: 0 },
    tricks_won: { north_south: 0, east_west: 0 },
    // 仅用于演示：每家展示用的“手里标签”列表（真实游戏中只对本家给出具体牌）
    demoHands: { NORTH: [] as string[], WEST: [] as string[], SOUTH: [] as string[], EAST: [] as string[] } as Record<Pos, string[]>,
  }),
  actions: {
    applySnapshot(s: any) {
      this.roomId = s.room_id || this.roomId
      this.phase = s.phase || this.phase
      this.dealer_position = (s.dealer_position as Pos) || this.dealer_position
      this.trump_suit = (s.trump_suit as any) ?? this.trump_suit
      this.dealt_count = s.dealt_count ?? this.dealt_count
      this.players = (s.players || []).map((p: any) => ({ id: p.id, name: p.name, position: p.position, cards_count: p.cards_count }))
      this.bottom_cards_count = s.bottom_cards_count ?? this.bottom_cards_count
      this.scores = s.scores || this.scores
      this.tricks_won = s.tricks_won || this.tricks_won
      // 如果快照包含我的手牌，可在此覆盖 demoHands[ME]
      if (Array.isArray(s.my_hand_sorted)) {
        // 前端需知道自己位置；此处略过，仅占位
      }
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
    applyPhaseChanged(e: { phase: 'waiting'|'dealing'|'bidding'|'playing' }) {
      this.phase = e.phase
    },
    applyScoreUpdated(e: { idle_score?: number; ns?: number; ew?: number; scores?: { north_south: number; east_west: number } }) {
      if (e.scores) this.scores = e.scores
      else {
        if (typeof e.ns === 'number') this.scores.north_south = e.ns
        if (typeof e.ew === 'number') this.scores.east_west = e.ew
      }
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
    resetDemoHands() {
      this.demoHands = { NORTH: [], WEST: [], SOUTH: [], EAST: [] }
      this.dealt_count = 0
    }
  },
})


