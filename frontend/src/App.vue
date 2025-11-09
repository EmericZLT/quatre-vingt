<template>
  <div class="min-h-screen bg-slate-900 text-slate-100">
    <div class="max-w-6xl mx-auto p-4">
      <header class="flex items-center justify-between py-2">
        <h1 class="text-xl font-semibold">八十分 | Quatre-Vingt</h1>
        <nav class="space-x-4 text-slate-300">
          <RouterLink to="/">桌面</RouterLink>
          <RouterLink to="/dealing">发牌演示</RouterLink>
          <RouterLink to="/rooms">房间列表</RouterLink>
          <RouterLink to="/game">牌局界面</RouterLink>
        </nav>
      </header>
      <main class="py-4">
        <RouterView />
      </main>
    </div>
  </div>
  
</template>

<script setup lang="ts"></script>

<style scoped>
a.router-link-active {
  color: #fff;
}
</style>

