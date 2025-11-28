<template>
  <div class="player-area" :class="{ 
    'current-player': isCurrentPlayer,
    'opponent-player': !isCurrentPlayer && position === 'NORTH'
  }">
    <!-- 玩家信息：当前玩家和对家显示在左侧，左右玩家显示在上方 -->
    <div 
      class="player-info" 
      :class="{ 
        'player-info-left': isCurrentPlayer || position === 'NORTH', 
        'player-info-top': !isCurrentPlayer && position !== 'NORTH' 
      }"
    >
      <div class="text-sm font-semibold text-white" :class="(isCurrentPlayer || position === 'NORTH') ? 'text-left' : 'text-center'">
        {{ displayName || (position === 'NORTH' ? '北' : position === 'SOUTH' ? '南' : position === 'EAST' ? '东' : '西') + '家' }}
      </div>
      <div class="text-xs text-amber-200" :class="(isCurrentPlayer || position === 'NORTH') ? 'text-left' : 'text-center'">{{ cardsCount }} 张</div>
    </div>

    <div class="hand-wrapper relative">
      <!-- 亮主牌展示 -->
      <div
        v-if="biddingCards.length"
        class="bidding-overlay"
        :class="biddingPlacementClass"
      >
        <div
          v-for="(card, idx) in biddingCards"
          :key="`bid-${idx}-${card}`"
          class="bidding-card"
        >
          <img :src="getCardImage(card)" :alt="card" />
        </div>
      </div>

      <!-- 当前轮次出牌展示（堆叠显示） -->
      <div
        v-if="sortedPlayedCards.length"
        class="played-cards-overlay"
        :class="playedCardsPlacementClass"
        :style="getPlayedCardsContainerStyle()"
      >
        <div
          v-for="(card, idx) in sortedPlayedCards"
          :key="`played-${idx}-${card}`"
          class="played-card"
          :style="getPlayedCardStyle(idx)"
        >
          <img :src="getCardImage(card)" :alt="card" />
        </div>
      </div>

      <!-- 准备状态显示（仅在scoring阶段显示） -->
      <div
        v-if="isReady && showReadyStatus"
        class="ready-status-overlay"
        :class="playedCardsPlacementClass"
      >
        <div class="ready-status-badge">
          <span class="ready-status-text">已准备</span>
        </div>
      </div>

      <!-- 手牌区域（堆叠显示） -->
      <div 
        class="hand-area relative" 
        :class="getHandAreaClass()"
        :style="getHandAreaStyle()"
      >
        <div 
          v-for="(card, index) in renderCards" 
          :key="`seat-${position}-idx-${index}`"
          class="card-stack-item"
          :class="{
            selectable: props.selectable && card !== '__BACK__',
            selected: isSelected(index),
            hovered: hoveredIndex === index && props.selectable && card !== '__BACK__',
            highlighted: isHighlighted(index)
          }"
          :style="getCardStyle(index)"
          @click="handleCardClick(index, card)"
          @mouseenter="handleMouseEnter(index, card)"
          @mouseleave="handleMouseLeave"
        >
          <img 
            :src="getCardImage(card)" 
            :alt="card"
            class="card-image"
            decoding="async"
            @error="handleImageError"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { getCardImageFromString, parseCardString } from '@/utils/cards'
import { throttle, debounce } from '@/utils/throttle'

interface Props {
  position: 'NORTH' | 'WEST' | 'SOUTH' | 'EAST'
  cards: string[]
  cardsCount: number
  isCurrentPlayer?: boolean
  displayName?: string
  biddingCards?: string[]
  playedCards?: string[]
  selectable?: boolean
  selectedIndices?: number[]
  isReady?: boolean
  showReadyStatus?: boolean
  highlightedCards?: string[]  // 需要高亮显示的牌（例如新加入的底牌）
}

const props = withDefaults(defineProps<Props>(), {
  isCurrentPlayer: false,
  displayName: '',
  biddingCards: () => [],
  playedCards: () => [],
  selectable: false,
  selectedIndices: () => [],
  isReady: false,
  showReadyStatus: false,
  highlightedCards: () => []
})

const emit = defineEmits<{
  (e: 'card-click', index: number): void
}>()

// 鼠标悬停状态（使用节流控制）
const hoveredIndex = ref<number | null>(null)
// 默认节流间隔：100ms（可根据体验调整）
const HOVER_THROTTLE_DELAY = 100
// 防抖延迟：50ms（用于 mouseleave，避免快速移动时立即清除）
const HOVER_DEBOUNCE_DELAY = 50

// 节流处理鼠标进入事件
const handleMouseEnterThrottled = throttle((index: number, cardStr: string) => {
  // 只有可选择的牌才响应悬停
  if (props.selectable && cardStr !== '__BACK__') {
    hoveredIndex.value = index
  }
}, HOVER_THROTTLE_DELAY)

// 防抖处理鼠标离开事件（避免快速移动时立即清除悬停状态）
const handleMouseLeaveDebounced = debounce(() => {
  hoveredIndex.value = null
}, HOVER_DEBOUNCE_DELAY)

function handleMouseEnter(index: number, cardStr: string) {
  // 取消待执行的离开事件（如果存在）
  handleMouseLeaveDebounced.cancel()
  handleMouseEnterThrottled(index, cardStr)
}

function handleMouseLeave() {
  handleMouseLeaveDebounced()
}

const biddingPlacementClass = computed(() => {
  switch (props.position) {
    case 'NORTH':
      return 'bidding-bottom'
    case 'SOUTH':
      return 'bidding-top'
    case 'WEST':
      return 'bidding-right'
    case 'EAST':
      return 'bidding-left'
    default:
      return 'bidding-bottom'
  }
})

const playedCardsPlacementClass = computed(() => {
  switch (props.position) {
    case 'NORTH':
      return 'played-cards-bottom'
    case 'SOUTH':
      return 'played-cards-top'
    case 'WEST':
      return 'played-cards-right'
    case 'EAST':
      return 'played-cards-left'
    default:
      return 'played-cards-bottom'
  }
})

// 渲染列表：若无具体手牌且有数量，则显示背面占位
const renderCards = computed<string[]>(() => {
  if (props.cards && props.cards.length > 0) return props.cards
  if (props.cardsCount > 0) return Array(props.cardsCount).fill('__BACK__')
  return []
})

// 对打出的牌进行排序（使用和手牌类似的排序逻辑）
const sortedPlayedCards = computed<string[]>(() => {
  if (!props.playedCards || props.playedCards.length === 0) return []
  
  // 解析卡牌字符串并排序
  const parsed = props.playedCards.map(card => {
    const parsed = parseCardString(card)
    return { card, parsed }
  }).filter(item => item.parsed !== null)
  
  // 简单排序：先按花色，再按点数
  // 花色优先级：♠ > ♥ > ♣ > ♦
  const suitPriority: Record<string, number> = { '♠': 4, '♥': 3, '♣': 2, '♦': 1 }
  const rankPriority: Record<string, number> = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14,
    'JOKER-B': 15, 'JOKER-A': 16
  }
  
  parsed.sort((a, b) => {
    const aParsed = a.parsed!
    const bParsed = b.parsed!
    
    // JOKER最大
    if (aParsed.rank === 'JOKER-A' || aParsed.rank === 'JOKER-B') {
      if (bParsed.rank !== 'JOKER-A' && bParsed.rank !== 'JOKER-B') return -1
      if (aParsed.rank === 'JOKER-A' && bParsed.rank === 'JOKER-B') return -1
      if (aParsed.rank === 'JOKER-B' && bParsed.rank === 'JOKER-A') return 1
      return 0
    }
    if (bParsed.rank === 'JOKER-A' || bParsed.rank === 'JOKER-B') return 1
    
    // 先按花色排序
    const aSuit = aParsed.suit || ''
    const bSuit = bParsed.suit || ''
    const suitDiff = (suitPriority[bSuit] || 0) - (suitPriority[aSuit] || 0)
    if (suitDiff !== 0) return suitDiff
    
    // 再按点数排序（从大到小）
    const aRank = rankPriority[aParsed.rank] || 0
    const bRank = rankPriority[bParsed.rank] || 0
    return bRank - aRank
  })
  
  return parsed.map(item => item.card)
})

// 获取卡牌图片
function getCardImage(cardStr: string): string {
  if (cardStr === '__BACK__') return '/assets/cards/Background.png'
  const img = getCardImageFromString(cardStr)
  return img || '/assets/cards/Background.png' // 默认背景图
}

// 处理图片加载错误
function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  img.src = '/assets/cards/Background.png'
}

// 根据位置获取手牌区域样式类
function getHandAreaClass(): string {
  const baseClass = 'hand-container'
  const positionClass = {
    'NORTH': 'hand-north',   // 上方，横向排列
    'SOUTH': 'hand-south',   // 下方，横向排列（当前玩家）
    'WEST': 'hand-west',     // 左侧，纵向排列
    'EAST': 'hand-east'      // 右侧，纵向排列
  }[props.position]
  return `${baseClass} ${positionClass}`
}

// 计算偏移量：当前玩家使用较大偏移（18px），其他玩家使用较小偏移（8px）以堆叠更紧密
const offsetStep = computed(() => {
  // 当前玩家的手牌需要看清楚，使用较大偏移
  // 其他玩家的背面牌可以堆叠更紧密
  return props.isCurrentPlayer ? 18 : 8
})

// 计算手牌总宽度（横向）或总高度（纵向）
const handTotalSize = computed(() => {
  const cardWidth = 60
  const cardHeight = 84
  const step = offsetStep.value
  
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向：总宽度 = 卡牌宽度 + (卡数-1) * 偏移量
    if (props.cards.length === 0) return cardWidth
    return cardWidth + (props.cards.length - 1) * step
  } else {
    // 纵向：总高度 = 卡牌高度 + (卡数-1) * 偏移量
    if (props.cards.length === 0) return cardHeight
    return cardHeight + (props.cards.length - 1) * step
  }
})

// 获取手牌区域的样式（动态调整大小）
function getHandAreaStyle(): Record<string, string> {
  // 当前玩家的手牌区域需要更大，其他玩家的可以更小
  const minSize = props.isCurrentPlayer ? 300 : 200
  const padding = props.isCurrentPlayer ? 40 : 20
  const cardWidth = 60 // 单张卡牌宽度
  
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向：根据卡牌数量调整宽度
    const calculatedWidth = Math.max(minSize, handTotalSize.value + padding)
    return {
      width: `${calculatedWidth}px`,
      minWidth: `${minSize}px`
    }
  } else {
    // 纵向：根据卡牌数量调整高度
    // 宽度设置为卡牌宽度，确保卡牌在容器内居中（通过 left: 50% + translateX(-50%)）
    const calculatedHeight = Math.max(minSize, handTotalSize.value + padding)
    return {
      height: `${calculatedHeight}px`,
      minHeight: `${minSize}px`,
      width: `${cardWidth}px` // 固定宽度为单张卡宽度，卡牌通过 left: 50% + translateX(-50%) 居中
    }
  }
}

// 获取每张卡的样式（实现堆叠效果）
function getCardStyle(index: number): Record<string, string> {
  const totalCards = props.cards.length
  if (totalCards === 0) return {}
  
  // 使用计算出的偏移量（当前玩家15px，其他玩家8px）
  const step = offsetStep.value
  const cardWidth = 60
  const cardHeight = 84
  
  // 检查是否悬停
  const isHovered = hoveredIndex.value === index && props.selectable
  
  // 根据位置确定堆叠方向
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向堆叠（左右方向）：后面的卡向右偏移
    const offset = index * step
    
    // 计算居中偏移：让整个手牌区域居中
    const totalWidth = handTotalSize.value
    const centerOffset = totalWidth / 2
    
    // 悬停时向上移动15px，保持垂直居中
    const transform = isHovered 
      ? 'translateY(calc(-50% - 15px))' 
      : 'translateY(-50%)'
    
    return {
      left: `calc(50% - ${centerOffset}px + ${offset}px)`,
      top: '50%',
      zIndex: `${index + 1}`, // 后面的卡在上层，保持堆叠顺序
      transform: transform
    }
  } else {
    // 纵向堆叠（上下方向）：后面的卡向下偏移
    const offset = index * step
    
    const totalHeight = handTotalSize.value
    const centerOffset = totalHeight / 2
    
    // 悬停时向上移动15px，保持水平居中
    const transform = isHovered 
      ? 'translateX(-50%) translateY(-15px)' 
      : 'translateX(-50%)'
    
    return {
      top: `calc(50% - ${centerOffset}px + ${offset}px)`,
      left: '50%',
      zIndex: `${index + 1}`, // 后面的卡在上层，保持堆叠顺序
      transform: transform
    }
  }
}

// 出牌卡牌堆叠样式（间隔15px，和手牌间距一样，大小和手牌一样）
const PLAYED_CARD_WIDTH = 60
const PLAYED_CARD_HEIGHT = 84
const PLAYED_CARD_SPACING = 15  // 改为和手牌间距一样

// 获取出牌卡牌容器样式
function getPlayedCardsContainerStyle(): Record<string, string> {
  const count = sortedPlayedCards.value.length
  if (count === 0) return {}
  
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向堆叠
    const totalWidth = PLAYED_CARD_WIDTH + (count - 1) * PLAYED_CARD_SPACING
    return {
      width: `${totalWidth}px`,
      height: `${PLAYED_CARD_HEIGHT}px`
    }
  } else {
    // 纵向堆叠
    const totalHeight = PLAYED_CARD_HEIGHT + (count - 1) * PLAYED_CARD_SPACING
    return {
      width: `${PLAYED_CARD_WIDTH}px`,
      height: `${totalHeight}px`
    }
  }
}

// 获取单张出牌卡牌样式
function getPlayedCardStyle(index: number): Record<string, string> {
  const count = sortedPlayedCards.value.length
  if (count === 0) return {}
  
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向堆叠（左右方向）
    const totalWidth = PLAYED_CARD_WIDTH + (count - 1) * PLAYED_CARD_SPACING
    const centerOffset = totalWidth / 2
    const offset = index * PLAYED_CARD_SPACING
    
    return {
      position: 'absolute',
      left: `calc(50% - ${centerOffset}px + ${offset}px)`,
      top: '50%',
      width: `${PLAYED_CARD_WIDTH}px`,
      height: `${PLAYED_CARD_HEIGHT}px`,
      zIndex: `${index + 1}`,
      transform: 'translateY(-50%)'
    }
  } else {
    // 纵向堆叠（上下方向）
    const totalHeight = PLAYED_CARD_HEIGHT + (count - 1) * PLAYED_CARD_SPACING
    const centerOffset = totalHeight / 2
    const offset = index * PLAYED_CARD_SPACING
    
    return {
      position: 'absolute',
      top: `calc(50% - ${centerOffset}px + ${offset}px)`,
      left: '50%',
      width: `${PLAYED_CARD_WIDTH}px`,
      height: `${PLAYED_CARD_HEIGHT}px`,
      zIndex: `${index + 1}`,
      transform: 'translateX(-50%)'
    }
  }
}

function isSelected(index: number): boolean {
  return Array.isArray(props.selectedIndices) && props.selectedIndices.includes(index)
}

function isHighlighted(index: number): boolean {
  if (!props.highlightedCards || props.highlightedCards.length === 0) return false
  const card = props.cards[index]
  if (!card || card === '__BACK__') return false
  
  // 统计高亮列表中每张牌的数量
  const highlightedCardCounts = new Map<string, number>()
  for (const c of props.highlightedCards) {
    highlightedCardCounts.set(c, (highlightedCardCounts.get(c) || 0) + 1)
  }
  
  // 统计当前索引之前已经高亮的相同牌的数量
  let countBeforeIndex = 0
  for (let i = 0; i < index; i++) {
    if (props.cards[i] === card) {
      // 检查这张牌是否应该被高亮（基于数量限制）
      const requiredCount = highlightedCardCounts.get(card) || 0
      if (countBeforeIndex < requiredCount) {
        countBeforeIndex++
      }
    }
  }
  
  // 检查当前牌是否应该被高亮（还有剩余配额）
  const requiredCount = highlightedCardCounts.get(card) || 0
  return countBeforeIndex < requiredCount
}

function handleCardClick(index: number, cardStr: string) {
  if (!props.selectable || cardStr === '__BACK__') return
  emit('card-click', index)
}

</script>

<style scoped>
.player-area {
  min-width: 200px;
  max-width: 100%;
  /* 确保手牌区域不会超出父容器 */
  overflow: visible;
}

/* 当前玩家和对家：使用 flex 布局，信息在左侧 */
.player-area.current-player,
.player-area.opponent-player {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 玩家信息：默认在上方（其他玩家） */
.player-info {
  min-height: 36px;
  flex-shrink: 0;
}

/* 当前玩家：信息在左侧 */
.player-info.player-info-left {
  min-width: 80px;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* 其他玩家：信息在上方 */
.player-info.player-info-top {
  margin-bottom: 8px;
}

.hand-wrapper {
  position: relative;
  flex: 1;
}

.bidding-overlay {
  position: absolute;
  display: flex;
  gap: 4px;
  pointer-events: none;
}

.bidding-overlay.bidding-top {
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.bidding-overlay.bidding-bottom {
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.bidding-overlay.bidding-left {
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  flex-direction: column;
}

.bidding-overlay.bidding-right {
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  flex-direction: column;
}

.bidding-card {
  width: 42px;
  height: 58px;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid rgba(250, 204, 21, 0.7);
  background: rgba(30, 41, 59, 0.8);
}

.bidding-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.played-cards-overlay {
  position: absolute;
  pointer-events: none;
  z-index: 15;
}

.played-cards-overlay.played-cards-top {
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.played-cards-overlay.played-cards-bottom {
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.played-cards-overlay.played-cards-left {
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.played-cards-overlay.played-cards-right {
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.played-card {
  position: absolute;
  height: 58px;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid rgba(34, 197, 94, 0.7);
  background: rgba(30, 41, 59, 0.8);
}

.played-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hand-area {
  position: relative;
  min-height: 80px;
  min-width: 120px;
  /* 确保手牌区域显示在已打出的牌（z-index: 15）之上 */
  z-index: 25;
}

/* 横向排列（北、南） */
.hand-north,
.hand-south {
  position: relative;
  height: 84px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: visible;
}

/* 纵向排列（东、西） */
.hand-west,
.hand-east {
  position: relative;
  /* width 由 getHandAreaStyle() 动态设置，确保居中 */
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: visible;
  /* 确保在父容器中水平居中 */
  margin-left: auto;
  margin-right: auto;
}

.card-stack-item {
  position: absolute;
  width: 60px;
  height: 84px;
  /* 只显示左上25%区域 */
  overflow: hidden;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  transition: all 0.2s ease;
  cursor: default;
  background: rgba(0, 0, 0, 0.1);
}

.card-stack-item.selectable {
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.4);
}

.card-stack-item.selectable.hovered {
  /* transform 已在 getCardStyle 中处理，这里只设置阴影效果 */
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.45);
  /* 不改变 z-index，保持原有堆叠顺序（左边的牌在下方，右边的牌在上方） */
}

.card-stack-item.selected {
  outline: 2px solid rgba(16, 185, 129, 0.9);
  outline-offset: 2px;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
  /* 不改变 z-index，保持原有堆叠顺序（左边的牌在下方，右边的牌在上方） */
}

.card-stack-item.highlighted {
  /* 醒目的橙色边框和背景，表示新加入的底牌 */
  border: 2px solid #f97316 !important;
  background: rgba(249, 115, 22, 0.2) !important;
  /* box-shadow: 0 0 0 1px #ffffff, 0 4px 16px rgba(249, 115, 22, 0.6) !important; */
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
  display: block;
  /* 降低闪烁：启用合成层与背面不可见 */
  will-change: transform;
  backface-visibility: hidden;
  transform: translateZ(0);
}

.empty-hand {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
}

.ready-status-overlay {
  position: absolute;
  pointer-events: none;
  z-index: 20;
}

.ready-status-overlay.played-cards-top {
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.ready-status-overlay.played-cards-bottom {
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.ready-status-overlay.played-cards-left {
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.ready-status-overlay.played-cards-right {
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.ready-status-badge {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.95), rgba(16, 185, 129, 0.95));
  border: 2px solid rgba(34, 197, 94, 1);
  border-radius: 8px;
  padding: 8px 16px;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4);
}

.ready-status-text {
  color: white;
  font-weight: bold;
  font-size: 14px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
}
</style>

