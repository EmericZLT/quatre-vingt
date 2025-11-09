<template>
  <div class="space-y-4">
    <div class="text-lg">欢迎进入牌桌</div>
    <div class="text-sm text-slate-300">此处将展示实时对局、手牌与计分。</div>

    <div class="p-3 rounded bg-slate-800 space-y-2">
      <div class="font-semibold">WebSocket 连接</div>
      <div class="flex gap-2 items-center">
        <input v-model="url" class="px-2 py-1 rounded text-black w-[420px]" placeholder="ws://127.0.0.1:8000/ws/game/demo" />
        <button class="px-3 py-1 rounded bg-emerald-600" @click="connect">连接</button>
        <button class="px-3 py-1 rounded bg-slate-600" @click="disconnect">断开</button>
        <span class="text-sm" :class="connected ? 'text-emerald-400':'text-red-400'">{{ connected ? '已连接' : '未连接' }}</span>
      </div>
      <div v-if="connected" class="flex gap-2 flex-wrap">
        <button class="px-3 py-1 rounded bg-blue-600 text-sm" @click="sendStartGame">开始游戏</button>
        <button class="px-3 py-1 rounded bg-blue-600 text-sm" @click="sendDealTick">发一张牌</button>
        <button class="px-3 py-1 rounded bg-blue-600 text-sm" @click="sendAutoDeal">自动发牌</button>
      </div>
      <div class="text-sm text-slate-300">日志（最近200条）：</div>
      <div class="h-40 overflow-auto bg-slate-900/60 rounded p-2 text-xs leading-6">
        <div v-for="(l,i) in log" :key="i">{{ l }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useWsStore } from '@/stores/ws'

const ws = useWsStore()
const { connected, log } = storeToRefs(ws)
const url = ref(ws.url)
watch(url, v => { ws.url = v })

function connect(){ ws.connect(url.value) }
function disconnect(){ ws.disconnect() }
function sendStartGame(){ ws.send({ type: 'start_game' }) }
function sendDealTick(){ ws.send({ type: 'deal_tick' }) }
function sendAutoDeal(){ ws.send({ type: 'auto_deal' }) }
</script>

