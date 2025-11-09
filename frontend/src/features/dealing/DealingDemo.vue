<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2">
      <button class="px-3 py-1 rounded bg-emerald-600" @click="start">开始发牌演示</button>
      <button class="px-3 py-1 rounded bg-slate-600" @click="reset">重置</button>
      <label class="text-sm flex items-center gap-1">
        <input type="checkbox" v-model="useBackend" /> 使用后端WS
      </label>
      <div class="text-sm text-slate-300">已发：{{ dealtCount }} / 100</div>
    </div>
    <div class="grid grid-cols-4 gap-4">
      <div v-for="pos in positions" :key="pos" class="p-3 rounded bg-slate-800 min-h-[120px]">
        <div class="font-semibold mb-2">{{ pos }}</div>
        <div class="flex flex-wrap gap-1">
          <Card v-for="(c, i) in hands[pos]" :key="i" :label="c" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { storeToRefs } from 'pinia'
import Card from '@/components/Card.vue'
import { useWsStore } from '@/stores/ws'
import { useGameStore } from '@/stores/game'

const positions = ['NORTH','WEST','SOUTH','EAST'] as const
type Pos = typeof positions[number]

const hands = ref<Record<Pos, string[]>>({
  NORTH: [], WEST: [], SOUTH: [], EAST: []
})
const dealtCount = ref(0)
const timer = ref<number | null>(null)
const useBackend = ref(false)
const ws = useWsStore()
const game = useGameStore()

// 使用 storeToRefs 来响应式地读取 store 状态
const { dealt_count: gameDealtCount, demoHands: gameDemoHands } = storeToRefs(game)

function tick() {
  if (dealtCount.value >= 100) {
    stop()
    return
  }
  const pos = positions[dealtCount.value % 4]
  // 用简化的牌面字符串演示。后续接后端 deal_tick 事件替换
  const label = `#${String(dealtCount.value + 1).padStart(2,'0')}`
  hands.value[pos] = [...hands.value[pos], label]
  dealtCount.value += 1
}

async function start() {
  stop()
  if (useBackend.value) {
    // 确保连接到正确的 URL（和桌面页一致）
    if (!ws.connected) {
      ws.connect(ws.url || 'ws://127.0.0.1:8000/ws/game/demo')
      // 等待连接成功
      await new Promise((resolve) => {
        const checkConnected = setInterval(() => {
          if (ws.connected) {
            clearInterval(checkConnected)
            resolve(true)
          }
        }, 100)
        // 超时保护
        setTimeout(() => {
          clearInterval(checkConnected)
          resolve(false)
        }, 5000)
      })
    }
    
    if (ws.connected) {
      // 重置状态
      game.resetDemoHands()
      console.log('[DealingDemo] Sending start_game')
      ws.send({ type: 'start_game' })
      // 等待 start_game 完成（通过 phase 变化或延迟）
      await new Promise(resolve => setTimeout(resolve, 1500))
      console.log('[DealingDemo] Sending auto_deal')
      ws.send({ type: 'auto_deal' })
    } else {
      console.error('[DealingDemo] WS not connected')
    }
  } else {
    timer.value = window.setInterval(tick, 200)
  }
}

// 监听 gameStore 的变化，实时更新手牌
watch([gameDealtCount, gameDemoHands], (newVal, oldVal) => {
  if (useBackend.value) {
    console.log('[DealingDemo] GameStore updated:', {
      dealt_count: gameDealtCount.value,
      hands: Object.keys(gameDemoHands.value).map(k => ({ [k]: gameDemoHands.value[k as Pos].length }))
    })
    // 创建新对象确保响应式更新
    hands.value = {
      NORTH: [...gameDemoHands.value.NORTH],
      WEST: [...gameDemoHands.value.WEST],
      SOUTH: [...gameDemoHands.value.SOUTH],
      EAST: [...gameDemoHands.value.EAST]
    }
    dealtCount.value = gameDealtCount.value
  }
}, { deep: true, immediate: true })

// 单独监听 dealt_count 变化，确保计数更新
watch(gameDealtCount, (newCount) => {
  if (useBackend.value) {
    dealtCount.value = newCount
  }
})

function stop() {
  if (timer.value) {
    clearInterval(timer.value)
    timer.value = null
  }
}
function reset() {
  stop()
  if (useBackend.value) {
    game.resetDemoHands()
  } else {
    hands.value = { NORTH: [], WEST: [], SOUTH: [], EAST: [] }
    dealtCount.value = 0
  }
}
</script>

