<template>
  <div class="game-table-container min-h-screen bg-gradient-to-br from-green-900 to-green-800 p-4">
    <!-- 顶部控制栏 -->
    <div class="max-w-7xl mx-auto mb-4">
      <div class="bg-slate-900/80 rounded-lg p-4 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <h2 class="text-xl font-bold text-white">牌局界面</h2>
          <div class="text-sm text-slate-300" v-if="roomName">
            房间：<span class="font-semibold text-white">{{ roomName }}</span>
          </div>
          <div class="text-sm text-slate-300">
            已发牌：<span class="font-semibold text-white">{{ dealtCount }}</span> / 100
          </div>
          <div class="text-sm text-slate-300">
            阶段：<span class="font-semibold text-white">{{ phase }}</span>
          </div>
          <div v-if="roomStore.playerName" class="text-sm text-slate-300">
            玩家：<span class="font-semibold text-white">{{ roomStore.playerName }}</span>
            <span class="text-xs ml-2">({{ myPosition }})</span>
          </div>
        </div>
        <div class="flex gap-2">
          <!-- 自动连接，无需手动按钮 -->
          <button v-if="false"></button>
          <template v-else>
            <button 
              @click="disconnect"
              class="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white text-sm"
            >
              断开连接
            </button>
            <button 
              v-if="isHost && (phase === 'waiting' || phase === 'dealing' || !phase)"
              @click="startGame"
              class="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm"
            >
              开始游戏
            </button>
            <button 
              v-if="isHost && phase === 'dealing'"
              @click="autoDeal"
              class="px-4 py-2 rounded bg-purple-600 hover:bg-purple-700 text-white text-sm"
            >
              自动发牌
            </button>
            <span v-if="!isHost" class="text-xs text-slate-400">仅房主可开始游戏</span>
          </template>
        </div>
      </div>
    </div>

    <!-- 牌桌主体 -->
    <div class="max-w-7xl mx-auto">
      <div class="relative bg-gradient-to-br from-amber-900 to-amber-800 rounded-3xl shadow-2xl p-8 min-h-[700px]">
        <!-- 左上角：级牌与主牌信息 -->
        <div class="absolute top-4 left-4 z-30 bg-slate-900/70 text-slate-100 rounded px-3 py-2 text-sm space-y-1 pointer-events-none">
          <div>当前级牌：<span class="font-semibold">{{ levelRankLabel }}</span></div>
          <div>主牌花色：<span class="font-semibold">{{ displayTrumpSuit }}</span></div>
          <div>当前最高：<span class="font-semibold">{{ displayCurrentBid }}</span></div>
        </div>
        <!-- 左上角：级牌与主牌 -->
        <div class="absolute top-4 left-4 z-30 bg-slate-900/70 text-slate-100 rounded px-3 py-2 text-sm space-y-1">
          <div>当前级牌：<span class="font-semibold">{{ currentLevel }}</span></div>
          <div>主牌花色：<span class="font-semibold">{{ trumpSuit || '未定' }}</span></div>
        </div>
        <!-- 中央区域（用于显示底牌、当前出牌等） -->
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div class="text-center">
            <div v-if="bottomCardsCount > 0" class="mb-4">
              <div class="text-sm text-amber-200 mb-2">底牌</div>
              <div class="text-2xl font-bold text-amber-100">{{ bottomCardsCount }} 张</div>
            </div>
          </div>
        </div>

        <!-- 顶部（上方） -->
        <div class="absolute top-8 left-1/2 transform -translate-x-1/2 z-20">
          <PlayerArea 
            position="NORTH"
            :cards="getPlayerHand(viewMap.top)"
            :cardsCount="getPlayerCardsCount(viewMap.top)"
            :isCurrentPlayer="false"
            :displayName="getSeatName(viewMap.top)"
            :biddingCards="getBiddingCards(viewMap.top)"
          />
        </div>

        <!-- 左侧 -->
        <div class="absolute left-8 top-1/2 transform -translate-y-1/2 z-20">
          <PlayerArea 
            position="WEST"
            :cards="getPlayerHand(viewMap.left)"
            :cardsCount="getPlayerCardsCount(viewMap.left)"
            :isCurrentPlayer="false"
            :displayName="getSeatName(viewMap.left)"
            :biddingCards="getBiddingCards(viewMap.left)"
          />
        </div>

        <!-- 底部（下方，当前玩家视角） -->
        <div class="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-20">
          <PlayerArea 
            position="SOUTH"
            :cards="getPlayerHand(viewMap.bottom)"
            :cardsCount="getPlayerCardsCount(viewMap.bottom)"
            :isCurrentPlayer="true"
            :displayName="getSeatName(viewMap.bottom)"
            :biddingCards="getBiddingCards(viewMap.bottom)"
          />

          <!-- 亮主/反主面板 -->
          <div v-if="showBiddingPanel" class="mt-4 bg-slate-900/70 rounded px-4 py-3 text-slate-100 w-full max-w-xl mx-auto">
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm">亮主 / 反主：选择要亮主的花色</div>
              <div class="text-xs text-slate-300">
                当前亮主：
                <span class="font-semibold">
                  {{ displayCurrentBid }}
                </span>
              </div>
            </div>
            <div class="flex gap-2 flex-wrap">
              <button
                class="px-3 py-1 rounded text-sm transition-colors"
                :class="bidOptions.noTrump ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-700 text-slate-400 opacity-50 cursor-not-allowed'"
                :disabled="disableBidding || !bidOptions.noTrump"
                @click="handleBid('NO_TRUMP')"
              >
                无主
              </button>
              <button
                v-for="suit in suitButtons"
                :key="`bid-${suit}`"
                class="px-3 py-1 rounded text-sm transition-colors"
                :class="bidOptions.suits[suit] ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-700 text-slate-400 opacity-50 cursor-not-allowed'"
                :disabled="disableBidding || !bidOptions.suits[suit]"
                @click="handleBid(suit)"
              >
                {{ suit }}
              </button>
              <button
                v-if="turnPlayerId === playerId"
                class="px-3 py-1 rounded bg-slate-600 hover:bg-slate-500 text-sm"
                @click="passBid"
              >
                过
              </button>
            </div>
          </div>
        </div>

        <!-- 右侧 -->
        <div class="absolute right-8 top-1/2 transform -translate-y-1/2 z-20">
          <PlayerArea 
            position="EAST"
            :cards="getPlayerHand(viewMap.right)"
            :cardsCount="getPlayerCardsCount(viewMap.right)"
            :isCurrentPlayer="false"
            :displayName="getSeatName(viewMap.right)"
            :biddingCards="getBiddingCards(viewMap.right)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { useWsStore } from '@/stores/ws'
import { useGameStore } from '@/stores/game'
import { useRoomStore } from '@/stores/room'
import PlayerArea from './PlayerArea.vue'

type Pos = 'NORTH' | 'WEST' | 'SOUTH' | 'EAST'

const route = useRoute()
const router = useRouter()
const ws = useWsStore()
const game = useGameStore()
const roomStore = useRoomStore()

const { connected, log } = storeToRefs(ws)
const { phase, dealt_count: dealtCount, players, bottom_cards_count: bottomCardsCount } = storeToRefs(game)

// 从路由或store获取房间ID和玩家ID
const roomId = computed(() => (route.params.roomId as string) || roomStore.roomId || 'demo')
const playerId = computed(() => roomStore.playerId)
const myPosition = computed(() => roomStore.playerPosition as Pos)
const roomName = computed(() => roomStore.roomName)
const isHost = computed(() => !!roomStore.ownerId && roomStore.ownerId === roomStore.playerId)
const canStart = computed(() => (Array.isArray(players.value) ? players.value.length : 0) === 4)
const currentLevel = ref<number | string>('?')
const trumpSuit = ref<string | null>(null)
const biddingStatus = ref<any>(null)
const showBiddingPanel = computed(() => phase.value === 'dealing' || phase.value === 'bidding')
const currentBid = computed(() => biddingStatus.value?.current_bid || null)
const turnPlayerId = computed<string | null>(() => biddingStatus.value?.turn_player_id ?? null)
const isOpenBidding = computed(() => !currentBid.value)
const biddingLockedForMe = computed(() => {
  if (!showBiddingPanel.value) return true
  const myId = playerId.value
  if (!myId) return true
  const turnId = turnPlayerId.value
  if (!turnId) {
    // 无当前亮主记录时允许自由亮主；若已有当前亮主，则等待轮询
    return !!currentBid.value
  }
  return turnId !== myId
})
const disableBidding = computed(() => biddingLockedForMe.value)
const displayTrumpSuit = computed(() => {
  if (trumpSuit.value) return trumpSuit.value
  const bid = currentBid.value
  if (!bid || !bid.bid_type) return '未定'
  if (bid.bid_type === 'double_joker' || bid.bid_type === 'double_big_joker') return '无主'
  return bid.suit || '未定'
})

const suitButtons = ['♠', '♥', '♣', '♦'] as const

const biddingCardsRaw = ref<Record<string, string[]>>({})
const biddingCardsByPos = computed(() => {
  const map: { NORTH: string[]; WEST: string[]; SOUTH: string[]; EAST: string[] } = {
    NORTH: [],
    WEST: [],
    SOUTH: [],
    EAST: []
  }
  const raw = biddingCardsRaw.value
  ;(players.value || []).forEach((p: any) => {
    const pos = (p.position as string)?.toUpperCase()
    if (pos && raw[p.id]) {
      if (pos === 'NORTH' || pos === 'WEST' || pos === 'SOUTH' || pos === 'EAST') {
        map[pos] = raw[p.id]
      }
    }
  })
  return map
})
function getBiddingCards(pos: Pos): string[] {
  return biddingCardsByPos.value[pos] || []
}

const levelRankLabel = computed(() => {
  const val = currentLevel.value
  if (typeof val !== 'number') return '?'
  if (val >= 2 && val <= 10) return String(val)
  const map: Record<number, string> = { 11: 'J', 12: 'Q', 13: 'K', 14: 'A' }
  return map[val] || '?'
})

type SuitSymbol = typeof suitButtons[number]

type HandInfo = {
  levelIndices: Record<SuitSymbol, number[]>
  smallJokerIdx: number[]
  bigJokerIdx: number[]
}

const handInfo = computed<HandInfo>(() => {
  const level = levelRankLabel.value
  const levelIndices: Record<SuitSymbol, number[]> = {
    '♠': [],
    '♥': [],
    '♣': [],
    '♦': []
  }
  const smallJokerIdx: number[] = []
  const bigJokerIdx: number[] = []
  myHand.value.forEach((card, idx) => {
    if (card.includes('JOKER-A')) bigJokerIdx.push(idx)
    else if (card.includes('JOKER-B')) smallJokerIdx.push(idx)
    else {
      const suit = card.slice(-1) as SuitSymbol
      const rank = card.slice(0, -1)
      if (rank === level && levelIndices[suit]) {
        levelIndices[suit].push(idx)
      }
    }
  })
  return { levelIndices, smallJokerIdx, bigJokerIdx }
})

const priorityMap: Record<string, number> = {
  single_level: 1,
  pair_level: 2,
  double_joker: 3,
  double_big_joker: 4,
}
const suitPriority: Record<SuitSymbol, number> = { '♦': 1, '♣': 2, '♥': 3, '♠': 4 }

interface CandidateBid {
  cards: string[]
  bid_type: 'single_level' | 'pair_level' | 'double_joker' | 'double_big_joker'
  suit?: SuitSymbol | null
  priority: number
  player_id?: string | null
}

const currentBidInfo = computed<CandidateBid | null>(() => {
  const bid = currentBid.value
  if (!bid || !bid.bid_type) return null
  return {
    cards: [],
    bid_type: bid.bid_type,
    suit: (bid.suit || null) as SuitSymbol | null,
    priority: priorityMap[bid.bid_type] ?? 0,
    player_id: bid.player_id || null,
  }
})

function canOverride(candidate: CandidateBid | null): boolean {
  if (!candidate) return false
  const current = currentBidInfo.value
  if (!current) return true
  if (candidate.priority > current.priority) return true
  if (candidate.priority < current.priority) return false
  if (candidate.bid_type === 'pair_level' && current.bid_type === 'pair_level') {
    const candSuit = candidate.suit as SuitSymbol | undefined
    const currSuit = current.suit as SuitSymbol | undefined
    if (!candSuit || !currSuit) return false
    const candPriority = suitPriority[candSuit] ?? 0
    const currPriority = suitPriority[currSuit] ?? 0
    return candPriority > currPriority
  }
  return false
}

function pickLevelCards(indices: number[], count: number): string[] | null {
  if (indices.length < count) return null
  return indices.slice(0, count).map(i => myHand.value[i])
}

function candidateForSuit(suit: SuitSymbol): CandidateBid | null {
  if (!showBiddingPanel.value) return null
  const indices = handInfo.value.levelIndices[suit]
  const combos: CandidateBid[] = []
  const pairCards = pickLevelCards(indices, 2)
  if (pairCards) {
    combos.push({ cards: pairCards, bid_type: 'pair_level', suit, priority: priorityMap['pair_level'] })
  }
  const singleCard = pickLevelCards(indices, 1)
  if (singleCard) {
    combos.push({ cards: singleCard, bid_type: 'single_level', suit, priority: priorityMap['single_level'] })
  }
  for (const combo of combos) {
    if (canOverride(combo)) return combo
  }
  return null
}

function candidateForNoTrump(): CandidateBid | null {
  if (!showBiddingPanel.value) return null
  const combos: CandidateBid[] = []
  if (handInfo.value.bigJokerIdx.length >= 2) {
    const idx = handInfo.value.bigJokerIdx
    combos.push({
      cards: [myHand.value[idx[0]], myHand.value[idx[1]]],
      bid_type: 'double_big_joker',
      priority: priorityMap['double_big_joker']
    })
  }
  if (handInfo.value.smallJokerIdx.length >= 2) {
    const idx = handInfo.value.smallJokerIdx
    combos.push({
      cards: [myHand.value[idx[0]], myHand.value[idx[1]]],
      bid_type: 'double_joker',
      priority: priorityMap['double_joker']
    })
  }
  for (const combo of combos) {
    if (canOverride(combo)) return combo
  }
  return null
}

const bidOptions = computed(() => {
  if (disableBidding.value) {
    return {
      noTrump: null as CandidateBid | null,
      suits: { '♠': null, '♥': null, '♣': null, '♦': null } as Record<SuitSymbol, CandidateBid | null>
    }
  }
  return {
    noTrump: candidateForNoTrump(),
    suits: {
      '♠': candidateForSuit('♠'),
      '♥': candidateForSuit('♥'),
      '♣': candidateForSuit('♣'),
      '♦': candidateForSuit('♦'),
    } as Record<SuitSymbol, CandidateBid | null>
  }
})

function handleBid(option: 'NO_TRUMP' | SuitSymbol) {
  if (disableBidding.value) return
  let candidate: CandidateBid | null = null
  if (option === 'NO_TRUMP') candidate = bidOptions.value.noTrump
  else candidate = bidOptions.value.suits[option]
  if (!candidate) return
  ws.send({ type: 'make_bid', cards: candidate.cards })
}

function passBid() {
  if (disableBidding.value) return
  ws.send({ type: 'pass_bid' })
}

function finishBidding() {
  ws.send({ type: 'finish_bidding' })
}

const playerNameMap = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  ;(players.value || []).forEach((p: any) => {
    map[p.id] = p.name
  })
  return map
})

const displayCurrentBid = computed(() => {
  const bid = currentBidInfo.value
  if (!bid) return '暂无'
  const playerKey = bid.player_id ?? ''
  const name = playerKey ? (playerNameMap.value[playerKey] || '未知玩家') : '未知玩家'
  const typeLabel: Record<CandidateBid['bid_type'], string> = {
    single_level: '单张级牌',
    pair_level: '级牌对子',
    double_joker: '双小王',
    double_big_joker: '双大王'
  }
  const suit = bid.suit ? `${bid.suit}` : '无主'
  return `${name} - ${suit} ${typeLabel[bid.bid_type]}`
})

// 座位名称（玩家名或空座位）
function getSeatName(pos: Pos): string {
  const p = (players.value || []).find(x => (x.position as string)?.toUpperCase() === pos)
  return p?.name || '(空座位)'
}

// 视角映射：保证当前玩家位于底部（SOUTH），其余座位相对旋转
const viewMap = computed<{ top: Pos; left: Pos; bottom: Pos; right: Pos }>(() => {
  const me = myPosition.value
  // 默认（我在SOUTH）：top=NORTH, left=WEST, bottom=SOUTH, right=EAST
  if (me === 'SOUTH' || !me) return { top: 'NORTH', left: 'WEST', bottom: 'SOUTH', right: 'EAST' }
  if (me === 'WEST')  return { top: 'EAST',  left: 'NORTH', bottom: 'WEST',  right: 'SOUTH' }
  if (me === 'NORTH') return { top: 'SOUTH', left: 'EAST',  bottom: 'NORTH', right: 'WEST' }
  // me === 'EAST'
  return { top: 'WEST', left: 'SOUTH', bottom: 'EAST', right: 'NORTH' }
})

// 玩家手牌（存储卡牌字符串）- 只存储自己的手牌
const myHand = ref<string[]>([])

// 所有玩家的手牌数量（用于显示卡背和计数）
const playersCardsCount = ref<Record<Pos, number>>({
  NORTH: 0,
  WEST: 0,
  SOUTH: 0,
  EAST: 0
})

// 获取玩家手牌数量
function getPlayerCardsCount(pos: Pos): number {
  if (pos === myPosition.value) {
    // 自己的手牌，返回实际数量
    return myHand.value.length
  } else {
    // 其他玩家的手牌，只返回数量
    return playersCardsCount.value[pos] ?? 0
  }
}

// 获取玩家手牌（只返回自己的手牌）
function getPlayerHand(pos: Pos): string[] {
  if (pos === myPosition.value) {
    return myHand.value
  }
  const count = playersCardsCount.value[pos] ?? 0
  return Array(count).fill('__BACK__')
}

// 连接WebSocket
function connect() {
  if (!playerId.value) {
    alert('请先加入房间')
    router.push('/rooms')
    return
  }
  // 构建WebSocket URL，包含player_id参数
  const wsUrl = `ws://127.0.0.1:8000/ws/game/${roomId.value}?player_id=${playerId.value}`
  ws.connect(wsUrl)
}

// 断开连接
function disconnect() {
  ws.disconnect()
}

// 清空手牌
function clearAllHands() {
  myHand.value = []
  playersCardsCount.value = {
    NORTH: 0,
    WEST: 0,
    SOUTH: 0,
    EAST: 0
  }
  // 同时清空gameStore中的手牌
  game.resetDemoHands()
}

// 开始游戏
function startGame() {
  if (ws.connected) {
    // 清空手牌
    clearAllHands()
    ws.send({ type: 'start_game' })
  }
}

// 自动发牌
function autoDeal() {
  if (ws.connected) {
    // 清空手牌
    clearAllHands()
    ws.send({ type: 'auto_deal' })
  }
}

// 监听WebSocket消息，更新手牌（优先使用排序后的手牌）
let messageHandler: ((msg: any) => void) | null = null

// 监听WebSocket消息
onMounted(() => {
  // 检查是否有房间和玩家信息
  if (!roomId.value || !playerId.value) {
    alert('请先加入房间')
    router.replace('/rooms')
    return
  }
  // 自动连接 WebSocket
  if (!connected.value) {
    connect()
  }
  
  messageHandler = (msg: any) => {
    if (msg.type === 'deal_tick') {
      const playerPos = (msg.player?.toUpperCase() as Pos) || null
      
      // 只更新自己的手牌
      if (playerPos === myPosition.value && msg.sorted_hand && Array.isArray(msg.sorted_hand)) {
        myHand.value = [...msg.sorted_hand]
      }
      // 使用后端提供的 players_cards_count 实时同步各家数量（含自己）
      if (msg.players_cards_count && typeof msg.players_cards_count === 'object') {
        const m = msg.players_cards_count as Record<string, number>
        const toPos = (k: string) => (k?.toUpperCase() as Pos)
        Object.keys(m).forEach(k => {
          const pos = toPos(k)
          if (pos) playersCardsCount.value[pos] = m[k]
        })
        if (myPosition.value) {
          playersCardsCount.value[myPosition.value] = myHand.value.length
        }
      }
    } else if (msg.type === 'state_snapshot') {
      if (typeof msg.current_level === 'number') currentLevel.value = msg.current_level
      trumpSuit.value = msg.trump_suit || null
      if (msg.bidding) {
        biddingStatus.value = { ...msg.bidding, turn_player_id: msg.turn_player_id ?? msg.bidding.turn_player_id ?? null }
      } else {
        biddingStatus.value = msg.turn_player_id ? { turn_player_id: msg.turn_player_id } : null
      }
      if (msg.bidding_cards) biddingCardsRaw.value = msg.bidding_cards
      if (typeof msg.room_name === 'string') {
        roomStore.updateRoomName(msg.room_name)
      }
      if (typeof msg.owner_id === 'string') {
        roomStore.updateOwner(msg.owner_id)
      }
      // 更新自己的手牌
      if (msg.my_hand && Array.isArray(msg.my_hand)) {
        myHand.value = [...msg.my_hand]
        if (myPosition.value) {
          playersCardsCount.value[myPosition.value] = myHand.value.length
        }
      }
      
      // 更新其他玩家的手牌数量（避免先清零造成闪烁）
      if (msg.players && Array.isArray(msg.players)) {
        msg.players.forEach((p: any) => {
          const pos = p.position?.toUpperCase() as Pos
          if (pos) {
            playersCardsCount.value[pos] = p.cards_count || 0
          }
        })
      }
      
      // 如果游戏重置，清空手牌
      if (msg.phase === 'waiting') {
        clearAllHands()
      }
    } else if (msg.type === 'phase_changed') {
      // 如果进入waiting阶段，清空手牌
      if (msg.phase === 'waiting') {
        clearAllHands()
      } else if (msg.phase === 'dealing') {
        // 进入发牌阶段时，确保手牌已清空（双重保险）
        clearAllHands()
      }
      if (msg.phase !== 'bidding') {
        biddingStatus.value = null
        biddingCardsRaw.value = {}
      }
    } else if (msg.type === 'bidding_updated') {
      biddingStatus.value = { ...(msg.bidding || {}), turn_player_id: msg.turn_player_id ?? msg.bidding?.turn_player_id ?? turnPlayerId.value }
      if (msg.bidding_cards) biddingCardsRaw.value = msg.bidding_cards
    }
  }
  
  if (messageHandler) {
    ws.on(messageHandler)
  }
})

onUnmounted(() => {
  if (messageHandler) {
    ws.off(messageHandler)
  }
})

// 监听dealt_count变化，如果重置则清空手牌
watch(dealtCount, (newCount, oldCount) => {
  if (newCount === 0 && oldCount > 0) {
    // 游戏重置
    clearAllHands()
  }
})

// 组件卸载时不需要特殊处理，因为watch会自动清理
</script>

<style scoped>
.game-table-container {
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(139, 69, 19, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(34, 139, 34, 0.3) 0%, transparent 50%);
}
</style>

