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
            阶段：<span class="font-semibold text-white">{{ phaseLabel }}</span>
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
            <button
              v-if="phase === 'playing' && lastTrickCards.length > 0"
              @click="openLastTrick"
              class="px-4 py-2 rounded bg-amber-600 hover:bg-amber-700 text-white text-sm"
            >
              上轮
            </button>
            <button
              v-if="isDealer && dealerHasBottomRef && bottomCardsCount > 0"
              @click="openBottomCards"
              class="px-4 py-2 rounded bg-purple-600 hover:bg-purple-700 text-white text-sm"
            >
              查看底牌
            </button>
            <span v-if="!isHost" class="text-xs text-slate-400">仅房主可开始游戏</span>
          </template>
        </div>
      </div>
    </div>

    <!-- 牌桌主体 -->
    <div class="max-w-7xl mx-auto">
      <div class="relative bg-gradient-to-br from-amber-900 to-amber-800 rounded-3xl shadow-2xl p-8 min-h-[700px]">
        <!-- 左上角：级牌、主牌、庄家信息 -->
        <div class="absolute top-4 left-4 z-30 bg-slate-900/80 text-slate-100 rounded px-3 py-2 text-sm space-y-1 pointer-events-none">
          <div>当前级牌：<span class="font-semibold">{{ levelRankLabel }}</span></div>
          <div>主牌花色：<span class="font-semibold">{{ displayTrumpSuit }}</span></div>
          <div>庄家：<span class="font-semibold">{{ dealerLabel }}</span></div>
          <div>当前最高：<span class="font-semibold">{{ displayCurrentBid }}</span></div>
          <div v-if="phase === 'bottom'" class="text-amber-200/80">扣底阶段：{{ bottomStatusText }}</div>
        </div>
        <!-- 右上角：闲家总得分 -->
        <div class="absolute top-4 right-4 z-30 bg-slate-900/80 text-slate-100 rounded px-3 py-2 text-sm space-y-1 pointer-events-none">
          <div class="text-amber-200 font-semibold mb-1">闲家得分</div>
          <div class="text-lg font-bold text-amber-300">{{ idleScoreTotal }}</div>
        </div>
        <!-- 中央区域（底牌已完全隐藏，通过右上角按钮查看） -->

        <!-- 顶部（上方） -->
        <div class="absolute top-8 left-1/2 transform -translate-x-1/2 z-20">
          <PlayerArea 
            position="NORTH"
            :cards="getPlayerHand(viewMap.top)"
            :cardsCount="getPlayerCardsCount(viewMap.top)"
            :isCurrentPlayer="false"
            :displayName="getSeatName(viewMap.top)"
            :biddingCards="getBiddingCards(viewMap.top)"
            :playedCards="getPlayedCards(viewMap.top)"
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
            :playedCards="getPlayedCards(viewMap.left)"
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
            :playedCards="getPlayedCards(viewMap.bottom)"
            :selectable="isSelectingBottom || isSelectingCard"
            :selectedIndices="selectedCardIndices"
            @card-click="handleCardClick"
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
          <!-- 扣底面板（仅庄家） -->
          <div
            v-else-if="isDealer && phase === 'bottom'"
            class="mt-4 bg-slate-900/70 rounded px-4 py-3 text-slate-100 w-full max-w-xl mx-auto"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm">扣底：请选择 {{ requiredBottomCount }} 张牌放回底牌</div>
              <div class="text-xs text-slate-300">
                已选 <span class="font-semibold">{{ selectedBottomIndices.length }}</span> / {{ requiredBottomCount }}
              </div>
            </div>
            <div class="flex gap-2 justify-end">
              <button
                class="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-sm"
                @click="resetBottomSelection"
                :disabled="selectedBottomIndices.length === 0"
              >
                重置选择
              </button>
              <button
                class="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-700 text-sm text-white disabled:bg-slate-600 disabled:text-slate-300"
                :disabled="!canSubmitBottom || submittingBottom"
                @click="submitBottom"
              >
                {{ submittingBottom ? '提交中...' : '确认扣底' }}
              </button>
            </div>
          </div>
          <!-- 出牌面板（仅playing阶段且轮到当前玩家） -->
          <div
            v-if="phase === 'playing' && isMyTurn"
            class="mt-4 bg-slate-900/70 rounded px-4 py-3 text-slate-100 w-full max-w-xl mx-auto"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm">出牌：请选择要出的牌（单张、对子、连对或甩牌）</div>
              <div v-if="selectedCards.length > 0" class="text-xs text-amber-200">
                已选 <span class="font-semibold">{{ selectedCards.length }}</span> 张
              </div>
            </div>
            <!-- 错误信息显示 -->
            <div v-if="playError" class="mb-2 text-sm text-red-400 bg-red-900/30 px-2 py-1 rounded">
              {{ playError }}
            </div>
            <!-- 已选牌显示 -->
            <div v-if="selectedCards.length > 0" class="mb-2 flex gap-1 flex-wrap">
              <div
                v-for="(card, idx) in selectedCards"
                :key="`selected-${idx}`"
                class="w-10 h-14 rounded border-2 border-emerald-400 overflow-hidden"
              >
                <img :src="getCardImage(card)" :alt="card" class="w-full h-full object-cover" />
              </div>
            </div>
            <div class="flex gap-2 justify-end">
              <button
                class="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-sm"
                @click="selectedCardIndicesForPlay = []"
                :disabled="selectedCards.length === 0"
              >
                取消选择
              </button>
              <button
                class="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-700 text-sm text-white disabled:bg-slate-600 disabled:text-slate-300"
                :disabled="!canPlayCard"
                @click="playCard"
              >
                {{ playingCard ? '出牌中...' : '出牌' }}
              </button>
            </div>
          </div>
          <!-- 等待其他玩家出牌提示 -->
          <div
            v-else-if="phase === 'playing' && !isMyTurn"
            class="mt-4 bg-slate-900/70 rounded px-4 py-3 text-slate-100 w-full max-w-xl mx-auto text-center"
          >
            <div class="text-sm text-amber-200">
              等待 <span class="font-semibold">{{ getPlayerNameByPosition(currentPlayerPosition || 'NORTH') }}</span> 出牌
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
            :playedCards="getPlayedCards(viewMap.right)"
          />
        </div>
      </div>
    </div>
  </div>

  <!-- "查看底牌"弹窗 -->
  <div
    v-if="showBottomCards"
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    @click.self="closeBottomCards"
  >
    <div class="bg-slate-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-white">底牌</h3>
        <button
          @click="closeBottomCards"
          class="px-4 py-2 rounded bg-slate-600 hover:bg-slate-500 text-white text-sm"
        >
          关闭
        </button>
      </div>
      <div v-if="bottomCards && bottomCards.length > 0" class="flex gap-2 flex-wrap justify-center">
        <img
          v-for="(card, cardIdx) in bottomCards"
          :key="`bottom-card-${cardIdx}`"
          :src="getCardImage(card)"
          :alt="card"
          class="w-20 h-28 object-cover rounded border-2 border-amber-300/50 shadow-lg"
          @error="handleImageError"
        />
      </div>
      <div v-else class="text-slate-400 text-center py-8">
        暂无底牌
      </div>
    </div>
  </div>

  <!-- "上轮"查看弹窗 -->
  <div
    v-if="showLastTrick"
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    @click.self="closeLastTrick"
  >
    <div class="bg-slate-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-white">上一轮出牌</h3>
        <button
          @click="closeLastTrick"
          class="px-4 py-2 rounded bg-slate-600 hover:bg-slate-500 text-white text-sm"
        >
          关闭
        </button>
      </div>
      <div v-if="lastTrickCards.length > 0" class="space-y-4">
        <div
          v-for="(trickCard, idx) in lastTrickCards"
          :key="`last-trick-${idx}`"
          class="flex items-center gap-4 p-3 bg-slate-700/50 rounded"
        >
          <div class="text-base font-bold text-white min-w-[100px]">
            {{ getPlayerNameByPosition(trickCard.player_position as Pos) }}：
          </div>
          <div class="flex gap-2 flex-wrap">
            <img
              v-for="(card, cardIdx) in trickCard.cards"
              :key="`card-${cardIdx}`"
              :src="getCardImage(card)"
              :alt="card"
              class="w-16 h-22 object-cover rounded border-2 border-amber-300/50 shadow-lg"
              @error="handleImageError"
            />
          </div>
        </div>
      </div>
      <div v-else class="text-slate-400 text-center py-8">
        暂无上一轮出牌记录
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
import { getCardImageFromString } from '@/utils/cards'

type Pos = 'NORTH' | 'WEST' | 'SOUTH' | 'EAST'

const route = useRoute()
const router = useRouter()
const ws = useWsStore()
const game = useGameStore()
const roomStore = useRoomStore()

const { connected, log } = storeToRefs(ws)
const {
  phase,
  dealt_count: dealtCount,
  players,
  bottom_cards_count: bottomCardsCount,
  bottom_cards: bottomCards,
  dealer_position,
  dealer_player_id,
  dealer_has_bottom,
  bottom_pending,
  current_trick,
  last_trick,
  idle_score
} = storeToRefs(game)

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

// 当前轮次出牌（每个玩家出的牌）
const playedCardsByPos = computed(() => {
  const map: { NORTH: string[]; WEST: string[]; SOUTH: string[]; EAST: string[] } = {
    NORTH: [],
    WEST: [],
    SOUTH: [],
    EAST: []
  }
  const trick = current_trick.value || []
  trick.forEach((item: any) => {
    const pos = (item.player_position as string)?.toUpperCase()
    const cards = item.cards || (item.card ? [item.card] : [])
    if (pos && (pos === 'NORTH' || pos === 'WEST' || pos === 'SOUTH' || pos === 'EAST')) {
      map[pos] = cards
    }
  })
  return map
})
function getPlayedCards(pos: Pos): string[] {
  return playedCardsByPos.value[pos] || []
}

const levelRankLabel = computed(() => {
  const val = currentLevel.value
  if (typeof val !== 'number') return '?'
  if (val >= 2 && val <= 10) return String(val)
  const map: Record<number, string> = { 11: 'J', 12: 'Q', 13: 'K', 14: 'A' }
  return map[val] || '?'
})

const phaseLabel = computed(() => {
  const map: Record<string, string> = {
    waiting: '等待',
    dealing: '发牌',
    bidding: '亮主',
    bottom: '扣底',
    playing: '出牌'
  }
  return map[phase.value] || phase.value
})

const dealerPosition = computed<Pos | ''>(() => {
  const raw = dealer_position.value
  if (!raw) return ''
  return raw.toUpperCase() as Pos
})

const dealerPlayerIdRef = computed(() => dealer_player_id.value || '')
const dealerNameMap = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  ;(players.value || []).forEach((p: any) => {
    if (p.id) map[p.id] = p.name || ''
  })
  return map
})

function getPosLabel(pos: Pos | ''): string {
  switch (pos) {
    case 'NORTH': return '北家'
    case 'SOUTH': return '南家'
    case 'WEST': return '西家'
    case 'EAST': return '东家'
    default: return ''
  }
}

const dealerLabel = computed(() => {
  const pos = dealerPosition.value
  const name = dealerPlayerIdRef.value ? dealerNameMap.value[dealerPlayerIdRef.value] : ''
  const seat = getPosLabel(pos)
  if (name && seat) return `${name}（${seat}）`
  if (name) return name
  if (seat) return seat
  return '未定'
})

// 闲家得分（直接使用idle_score）
const idleScoreTotal = computed(() => {
  return idle_score.value || 0
})

const isDealer = computed(() => !!dealerPlayerIdRef.value && dealerPlayerIdRef.value === playerId.value)
const dealerHasBottomRef = computed(() => dealer_has_bottom.value)
const bottomPendingRef = computed(() => bottom_pending.value)
const isSelectingBottom = computed(() => phase.value === 'bottom' && isDealer.value && bottomPendingRef.value)
const requiredBottomCount = computed(() => bottomCardsCount.value || 8)
const selectedBottomIndices = ref<number[]>([])
const submittingBottom = ref(false)
const selectedBottomCards = computed(() =>
  selectedBottomIndices.value
    .map((idx) => myHand.value[idx])
    .filter((card): card is string => typeof card === 'string' && !!card)
)
const canSubmitBottom = computed(() => isSelectingBottom.value && selectedBottomCards.value.length === requiredBottomCount.value && !submittingBottom.value)
const bottomStatusText = computed(() => {
  if (!bottomPendingRef.value && dealerHasBottomRef.value) {
    return isDealer.value ? '扣底已提交' : '庄家已完成扣底'
  }
  if (isDealer.value) {
    return `请选择 ${requiredBottomCount.value} 张牌放回底牌`
  }
  return '等待庄家扣底'
})

// 底牌查看弹窗状态
const showBottomCards = ref(false)

function openBottomCards() {
  showBottomCards.value = true
}

function closeBottomCards() {
  showBottomCards.value = false
}

// 获取卡牌图片
function getCardImage(cardStr: string): string {
  if (cardStr === '__BACK__') {
    return '/assets/cards/Background.png'
  }
  const img = getCardImageFromString(cardStr)
  return img || '/assets/cards/Background.png'
}

// 处理图片加载错误
function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  img.src = '/assets/cards/Background.png'
}


// 根据位置获取玩家名称
function getPlayerNameByPosition(pos: Pos): string {
  const player = players.value.find(p => (p.position as string)?.toUpperCase() === pos)
  return player?.name || getPosLabel(pos)
}

// "上轮"查看功能
const showLastTrick = ref(false)
const lastTrickCards = computed(() => {
  return last_trick.value || []
})

function openLastTrick() {
  showLastTrick.value = true
}

function closeLastTrick() {
  showLastTrick.value = false
}

// 出牌选择功能（支持多张牌）
const currentPlayerPosition = computed(() => {
  const cp = game.current_player
  if (!cp) return null
  return cp.toUpperCase() as Pos
})
const isMyTurn = computed(() => {
  return phase.value === 'playing' && currentPlayerPosition.value === myPosition.value
})
const isSelectingCard = computed(() => phase.value === 'playing' && isMyTurn.value)
const selectedCardIndicesForPlay = ref<number[]>([])
const playingCard = ref(false)
const playError = ref<string | null>(null)

function toggleCardSelection(index: number) {
  if (!isSelectingCard.value) return
  const card = myHand.value[index]
  if (!card || card === '__BACK__') return
  
  const existingIndex = selectedCardIndicesForPlay.value.indexOf(index)
  if (existingIndex > -1) {
    selectedCardIndicesForPlay.value.splice(existingIndex, 1)
  } else {
    selectedCardIndicesForPlay.value.push(index)
  }
  playError.value = null // 清除错误信息
}

const selectedCards = computed(() => {
  return selectedCardIndicesForPlay.value
    .map((idx) => myHand.value[idx])
    .filter((card): card is string => typeof card === 'string' && !!card)
})

const canPlayCard = computed(() => {
  return isSelectingCard.value && selectedCards.value.length > 0 && !playingCard.value
})

// 主玩家选中的牌索引（用于PlayerArea）
const selectedCardIndices = computed(() => {
  if (isSelectingBottom.value) {
    return selectedBottomIndices.value
  }
  if (isSelectingCard.value) {
    return selectedCardIndicesForPlay.value
  }
  return []
})

async function playCard() {
  if (!canPlayCard.value || selectedCards.value.length === 0) return
  
  playingCard.value = true
  playError.value = null
  try {
    ws.send({ type: 'play_card', cards: selectedCards.value })
    // 不清空选择，等待后端确认成功后再清空
  } catch (error) {
    playError.value = '出牌失败，请重试'
    playingCard.value = false
  }
}

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

function handleCardClick(index: number) {
  if (isSelectingBottom.value) {
    toggleBottomCard(index)
  } else if (isSelectingCard.value) {
    toggleCardSelection(index)
  }
}

function toggleBottomCard(index: number) {
  if (!isSelectingBottom.value) return
  const current = [...selectedBottomIndices.value]
  const foundIdx = current.indexOf(index)
  if (foundIdx >= 0) {
    current.splice(foundIdx, 1)
  } else {
    if (current.length >= requiredBottomCount.value) return
    current.push(index)
  }
  selectedBottomIndices.value = current.sort((a, b) => a - b)
}

function resetBottomSelection() {
  selectedBottomIndices.value = []
  submittingBottom.value = false
}

function submitBottom() {
  if (!canSubmitBottom.value) return
  submittingBottom.value = true
  ws.send({ type: 'submit_bottom', cards: [...selectedBottomCards.value] })
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
      // 如果离开playing阶段，清空出牌选择
      if (msg.phase !== 'playing') {
        selectedCardIndicesForPlay.value = []
        playError.value = null
        playingCard.value = false
      }
    } else if (msg.type === 'bidding_updated') {
      biddingStatus.value = { ...(msg.bidding || {}), turn_player_id: msg.turn_player_id ?? msg.bidding?.turn_player_id ?? turnPlayerId.value }
      if (msg.bidding_cards) biddingCardsRaw.value = msg.bidding_cards
    } else if (msg.type === 'trick_complete') {
      // 轮次结束时清空选择
      selectedCardIndicesForPlay.value = []
      playError.value = null
    } else if (msg.type === 'card_played') {
      // 出牌后，如果是自己出的牌，清空选择
      if (msg.player_id === playerId.value) {
        selectedCardIndicesForPlay.value = []
        playError.value = null
        playingCard.value = false
      }
      // GameStore的applyCardPlayed会自动更新current_player，这里不需要额外操作
      // 但为了确保UI立即响应，可以强制触发一次更新检查
    } else if (msg.type === 'error') {
      // 处理错误信息（出牌失败等）
      if (msg.message) {
        playError.value = msg.message
        playingCard.value = false
        // 如果有forced_cards，可能需要处理甩牌失败的情况
        if (msg.forced_cards && Array.isArray(msg.forced_cards)) {
          // 甩牌失败，自动选择被强制出的牌
          const forcedIndices: number[] = []
          msg.forced_cards.forEach((forcedCard: string) => {
            const idx = myHand.value.findIndex(card => card === forcedCard)
            if (idx >= 0) {
              forcedIndices.push(idx)
            }
          })
          if (forcedIndices.length > 0) {
            selectedCardIndicesForPlay.value = forcedIndices
          }
        }
      }
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

watch(
  () => phase.value,
  (newPhase, oldPhase) => {
    if (newPhase === 'bottom' || oldPhase === 'bottom') {
      resetBottomSelection()
      submittingBottom.value = false
    }
  }
)

watch(bottomPendingRef, (pending) => {
  if (!pending) {
    submittingBottom.value = false
  }
})

watch(myHand, () => {
  if (!isSelectingBottom.value) {
    resetBottomSelection()
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

