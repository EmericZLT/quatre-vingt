<template>
  <div class="game-table-container min-h-screen bg-gradient-to-br from-green-900 to-green-800 p-4">
    <!-- 顶部控制栏 -->
    <div class="max-w-7xl mx-auto mb-4">
      <div class="bg-slate-900/80 rounded-lg p-4 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <h2 class="text-xl font-bold text-white">牌局界面</h2>
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
          <button 
            v-if="!connected"
            @click="connect"
            class="px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-sm"
          >
            连接服务器
          </button>
          <template v-else>
            <button 
              @click="disconnect"
              class="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white text-sm"
            >
              断开连接
            </button>
            <button 
              v-if="phase === 'waiting' || phase === 'dealing' || !phase"
              @click="startGame"
              class="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm"
            >
              开始游戏
            </button>
            <button 
              v-if="phase === 'dealing'"
              @click="autoDeal"
              class="px-4 py-2 rounded bg-purple-600 hover:bg-purple-700 text-white text-sm"
            >
              自动发牌
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- 牌桌主体 -->
    <div class="max-w-7xl mx-auto">
      <div class="relative bg-gradient-to-br from-amber-900 to-amber-800 rounded-3xl shadow-2xl p-8 min-h-[700px]">
        <!-- 中央区域（用于显示底牌、当前出牌等） -->
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div class="text-center">
            <div v-if="bottomCardsCount > 0" class="mb-4">
              <div class="text-sm text-amber-200 mb-2">底牌</div>
              <div class="text-2xl font-bold text-amber-100">{{ bottomCardsCount }} 张</div>
            </div>
          </div>
        </div>

        <!-- 北家（上方） -->
        <div class="absolute top-8 left-1/2 transform -translate-x-1/2 z-20">
          <PlayerArea 
            position="NORTH"
            :cards="getPlayerHand('NORTH')"
            :cardsCount="getPlayerCardsCount('NORTH')"
            :isCurrentPlayer="myPosition === 'NORTH'"
          />
        </div>

        <!-- 西家（左侧） -->
        <div class="absolute left-8 top-1/2 transform -translate-y-1/2 z-20">
          <PlayerArea 
            position="WEST"
            :cards="getPlayerHand('WEST')"
            :cardsCount="getPlayerCardsCount('WEST')"
            :isCurrentPlayer="myPosition === 'WEST'"
          />
        </div>

        <!-- 南家（下方，当前玩家视角） -->
        <div class="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-20">
          <PlayerArea 
            position="SOUTH"
            :cards="getPlayerHand('SOUTH')"
            :cardsCount="getPlayerCardsCount('SOUTH')"
            :isCurrentPlayer="myPosition === 'SOUTH'"
          />
        </div>

        <!-- 东家（右侧） -->
        <div class="absolute right-8 top-1/2 transform -translate-y-1/2 z-20">
          <PlayerArea 
            position="EAST"
            :cards="getPlayerHand('EAST')"
            :cardsCount="getPlayerCardsCount('EAST')"
            :isCurrentPlayer="myPosition === 'EAST'"
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

// 玩家手牌（存储卡牌字符串）- 只存储自己的手牌
const myHand = ref<string[]>([])

// 其他玩家的手牌数量（不显示具体牌）
const otherPlayersCardsCount = ref<Record<Pos, number>>({
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
    const player = players.value.find(p => p.position === pos)
    return player?.cards_count || otherPlayersCardsCount.value[pos] || 0
  }
}

// 获取玩家手牌（只返回自己的手牌）
function getPlayerHand(pos: Pos): string[] {
  if (pos === myPosition.value) {
    return myHand.value
  }
  return [] // 其他玩家不显示手牌
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
  otherPlayersCardsCount.value = {
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
    router.push('/rooms')
    return
  }
  
  messageHandler = (msg: any) => {
    if (msg.type === 'deal_tick') {
      const playerPos = (msg.player?.toUpperCase() as Pos) || null
      
      // 只更新自己的手牌
      if (playerPos === myPosition.value && msg.sorted_hand && Array.isArray(msg.sorted_hand)) {
        myHand.value = [...msg.sorted_hand]
      } else if (playerPos && playerPos !== myPosition.value) {
        // 更新其他玩家的手牌数量
        const player = players.value.find(p => p.position === playerPos)
        if (player) {
          otherPlayersCardsCount.value[playerPos] = player.cards_count
        }
      }
    } else if (msg.type === 'state_snapshot') {
      // 更新自己的手牌
      if (msg.my_hand && Array.isArray(msg.my_hand)) {
        myHand.value = [...msg.my_hand]
      }
      
      // 更新其他玩家的手牌数量
      if (msg.players && Array.isArray(msg.players)) {
        msg.players.forEach((p: any) => {
          const pos = p.position?.toUpperCase() as Pos
          if (pos && pos !== myPosition.value) {
            otherPlayersCardsCount.value[pos] = p.cards_count || 0
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

