<template>
  <div class="countdown-clock" :class="{ 'blink': isBlinking }">
    <div class="clock-icon">⏰</div>
    <div class="countdown-time">{{ countdown }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGameStore } from '@/stores/game'

const gameStore = useGameStore()

// 计算是否需要闪烁（最后5秒，且不是不限制时长）
const isBlinking = computed(() => {
  return gameStore.countdownActive && gameStore.countdown <= 5 && gameStore.play_time_limit > 0
})

// 计算倒计时时间（如果不限制时长，显示∞）
const countdown = computed(() => {
  // 如果 play_time_limit 为 0，表示不限制时长，显示 ∞
  if (gameStore.play_time_limit === 0) {
    return '∞'
  }
  return gameStore.countdown
})
</script>

<style scoped>
.countdown-clock {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #2d3748;
  color: white;
  border-radius: 9999px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  font-weight: bold;
  font-size: 1.25rem;
  transition: all 0.3s ease;
}

.clock-icon {
  font-size: 1.5rem;
}

.countdown-time {
  font-size: 1.5rem;
  font-family: 'Courier New', monospace;
}

/* 闪烁动画 */
.blink {
  animation: blink 1s infinite alternate;
}

@keyframes blink {
  from {
    background-color: #2d3748;
    color: white;
    transform: scale(1);
  }
  to {
    background-color: #e53e3e;
    color: white;
    transform: scale(1.1);
  }
}
</style>