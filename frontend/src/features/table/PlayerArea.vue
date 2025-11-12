<template>
  <div class="player-area" :class="{ 'current-player': isCurrentPlayer }">
    <!-- 玩家信息 -->
    <div class="player-info mb-2">
      <div class="text-sm font-semibold text-white text-center">
        {{ displayName || (position === 'NORTH' ? '北' : position === 'SOUTH' ? '南' : position === 'EAST' ? '东' : '西') + '家' }}
      </div>
      <div class="text-xs text-amber-200 text-center">{{ cardsCount }} 张</div>
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
          :style="getCardStyle(index)"
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
import { computed } from 'vue'
import { getCardImageFromString } from '@/utils/cards'

interface Props {
  position: 'NORTH' | 'WEST' | 'SOUTH' | 'EAST'
  cards: string[]
  cardsCount: number
  isCurrentPlayer?: boolean
  displayName?: string
  biddingCards?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  isCurrentPlayer: false,
  displayName: '',
  biddingCards: () => []
})

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

// 渲染列表：若无具体手牌且有数量，则显示背面占位
const renderCards = computed<string[]>(() => {
  if (props.cards && props.cards.length > 0) return props.cards
  if (props.cardsCount > 0) return Array(props.cardsCount).fill('__BACK__')
  return []
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

// 计算手牌总宽度（横向）或总高度（纵向）
const handTotalSize = computed(() => {
  const cardWidth = 60
  const cardHeight = 84
  const offsetStep = 15
  
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向：总宽度 = 卡牌宽度 + (卡数-1) * 偏移量
    if (props.cards.length === 0) return cardWidth
    return cardWidth + (props.cards.length - 1) * offsetStep
  } else {
    // 纵向：总高度 = 卡牌高度 + (卡数-1) * 偏移量
    if (props.cards.length === 0) return cardHeight
    return cardHeight + (props.cards.length - 1) * offsetStep
  }
})

// 获取手牌区域的样式（动态调整大小）
function getHandAreaStyle(): Record<string, string> {
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向：根据卡牌数量调整宽度
    const minWidth = 300
    const calculatedWidth = Math.max(minWidth, handTotalSize.value + 40) // 加40px边距
    return {
      width: `${calculatedWidth}px`,
      minWidth: `${minWidth}px`
    }
  } else {
    // 纵向：根据卡牌数量调整高度
    const minHeight = 300
    const calculatedHeight = Math.max(minHeight, handTotalSize.value + 40) // 加40px边距
    return {
      height: `${calculatedHeight}px`,
      minHeight: `${minHeight}px`
    }
  }
}

// 获取每张卡的样式（实现堆叠效果）
function getCardStyle(index: number): Record<string, string> {
  const totalCards = props.cards.length
  if (totalCards === 0) return {}
  
  // 每张卡偏移量：卡牌宽度60px的25%，即15px，这样后面的卡会覆盖前面卡的右侧75%
  const offsetStep = 15 // 每张卡的偏移量（px）
  const cardWidth = 60
  const cardHeight = 84
  
  // 根据位置确定堆叠方向
  if (props.position === 'NORTH' || props.position === 'SOUTH') {
    // 横向堆叠（左右方向）：后面的卡向右偏移，覆盖前面卡的右侧75%，露出左侧25%
    const offset = index * offsetStep
    
    // 计算居中偏移：让整个手牌区域居中
    const totalWidth = handTotalSize.value
    const centerOffset = totalWidth / 2
    
    return {
      left: `calc(50% - ${centerOffset}px + ${offset}px)`,
      top: '50%',
      zIndex: `${index + 1}`, // 后面的卡在上层
      transform: 'translateY(-50%)'
    }
  } else {
    // 纵向堆叠（上下方向）：后面的卡向下偏移，覆盖前面卡的下侧75%，露出上侧25%
    const offset = index * offsetStep
    
    const totalHeight = handTotalSize.value
    const centerOffset = totalHeight / 2
    
    return {
      top: `calc(50% - ${centerOffset}px + ${offset}px)`,
      left: '50%',
      zIndex: `${index + 1}`, // 后面的卡在上层
      transform: 'translateX(-50%)'
    }
  }
}

</script>

<style scoped>
.player-area {
  min-width: 200px;
  max-width: 100%;
  /* 确保手牌区域不会超出父容器 */
  overflow: visible;
}

.player-info {
  min-height: 36px;
}

.hand-wrapper {
  position: relative;
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

.hand-area {
  position: relative;
  min-height: 80px;
  min-width: 120px;
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
  width: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: visible;
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
  cursor: pointer;
  background: rgba(0, 0, 0, 0.1);
}

.card-stack-item:hover {
  transform: scale(1.1) !important;
  z-index: 9999 !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
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
</style>

