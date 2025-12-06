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

// 计算是否需要闪烁（最后5秒）
const isBlinking = computed(() => {
  return gameStore.countdownActive && gameStore.countdown <= 5
})

// 计算倒计时时间
const countdown = computed(() => {
  return gameStore.countdown
})
</script>

<style scoped>
.countdown-clock {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: rgba(100, 139, 112, 0.5);
  color: white;
  border-radius: 0.5rem;
  box-shadow: none;
  font-weight: bold;
  font-size: 1.1rem;
  transition: all 0.3s ease;
}

.clock-icon {
  font-size: 1.2rem;
  color: #fbbf24;
}

.countdown-time {
  font-size: 1.1rem;
  font-family: 'Courier New', monospace;
  color: #fbbf24;
  min-width: 1.5rem;
  text-align: center;
}

/* 闪烁动画 */
.blink {
  animation: blink 1s infinite alternate;
}

@keyframes blink {
  from {
    color: #fbbf24;
    background-color: rgba(100, 116, 139, 0.5);
    transform: scale(1);
  }
  to {
    color: #ffffff;
    background-color: #ef4444;
  }
}
</style>