<template>
  <div class="min-h-screen bg-slate-900 text-slate-100">
    <div class="max-w-6xl mx-auto p-4">
      <header class="flex items-center justify-between py-2">
        <h1 class="text-xl font-semibold">潘子爹团建 | Quatre-Vingt</h1>
        <nav class="space-x-4 text-slate-300">
          <RouterLink
            v-if="hasActiveRoom"
            :to="`/game/${roomStore.roomId}`"
          >
            牌局界面
          </RouterLink>
          <RouterLink
            v-else
            to="/rooms"
          >
            房间列表
          </RouterLink>
          <RouterLink
            v-if="isDev"
            to="/"
          >
            桌面
          </RouterLink>
          <RouterLink
            v-if="isDev"
            to="/dealing"
          >
            发牌演示
          </RouterLink>
        </nav>
      </header>
      <main class="py-4">
        <RouterView />
      </main>
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoomStore } from '@/stores/room'

const roomStore = useRoomStore()
const hasActiveRoom = computed(() => !!roomStore.roomId)
const isDev = import.meta.env.MODE === 'development'
</script>

<style scoped>
a.router-link-active {
  color: #fff;
}
</style>

